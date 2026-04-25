import asyncio
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.config import cfg
from core.env_loader import load_dev_env_if_needed
from core.log import logger

try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai 模块未安装，文章 AI 过滤功能不可用")


_RULES = [
    (
        "recruitment",
        re.compile(
            r"(招聘|内推|校招|社招|实习生|招聘会|岗位|offer|求职|投递|hr|面试|简历)",
            re.IGNORECASE,
        ),
    ),
    (
        "promotion",
        re.compile(
            r"(软广|软文|广告|推广|赞助|合作|抽奖|报名|活动|直播|预告|直播回放|福利|转发|限时|新品|招商)",
            re.IGNORECASE,
        ),
    ),
]


@dataclass
class ArticleFilterDecision:
    decision: str
    category: str
    confidence: float
    reason: str
    model_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "category": self.category,
            "confidence": self.confidence,
            "reason": self.reason,
            "model_name": self.model_name,
        }


class ArticleFilterEngine:
    """文章过滤引擎：先规则，再 OpenAI 兼容模型。"""

    def __init__(self) -> None:
        load_dev_env_if_needed()
        self.client = None
        self.model = None
        self.base_url = None
        self.api_key = None

        api_key_raw = cfg.get("openai.api_key", None, silent=True) or os.getenv("OPENAI_API_KEY", "")
        base_url_raw = cfg.get("openai.base_url", None, silent=True) or os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        model_raw = cfg.get("article_filter.model", None, silent=True) or cfg.get(
            "openai.model", None, silent=True
        ) or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        self.api_key = str(api_key_raw) if api_key_raw else ""
        self.base_url = str(base_url_raw) if base_url_raw else "https://api.openai.com/v1"
        self.model = str(model_raw) if model_raw else "gpt-4o-mini"

        if OPENAI_AVAILABLE and self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info("文章 AI 过滤器已启用，模型: %s, Base URL: %s", self.model, self.base_url)
        else:
            logger.warning(
                "文章 AI 过滤器未启用，api_key=%s, openai_available=%s",
                bool(self.api_key),
                OPENAI_AVAILABLE,
            )

    @staticmethod
    def _normalize_text(text: Optional[str]) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", str(text)).strip()

    def _rule_based(self, title: str, tags: List[str], source: str) -> Optional[ArticleFilterDecision]:
        normalized = " ".join([title, source, " ".join(tags)])
        for category, pattern in _RULES:
            if pattern.search(normalized):
                confidence = 0.96 if category == "recruitment" else 0.92
                reason = f"命中规则关键词: {pattern.pattern}"
                return ArticleFilterDecision(
                    decision="hide",
                    category=category,
                    confidence=confidence,
                    reason=reason,
                    model_name="rule-based",
                )
        return None

    async def classify(self, title: str, tags: List[str], source: str = "", description: str = "") -> ArticleFilterDecision:
        title = self._normalize_text(title)
        tags = [self._normalize_text(tag) for tag in tags if self._normalize_text(tag)]
        source = self._normalize_text(source)
        description = self._normalize_text(description)

        rule_result = self._rule_based(title, tags, source)
        if rule_result:
            return rule_result

        if not self.client:
            return ArticleFilterDecision(
                decision="keep",
                category="unknown",
                confidence=0.0,
                reason="未配置 OpenAI 兼容 API，已仅执行规则过滤",
                model_name="rule-only",
            )

        payload = {
            "title": title,
            "tags": tags,
            "source": source,
            "description": description[:300],
        }

        system_prompt = (
            "你是微信公众号信息流过滤器。"
            "任务是判断文章是否应在信息流里默认隐藏。"
            "只关注标题、标签、来源和简短描述。"
            "明显的软广、推广、活动报名、直播预告、招聘、内推、校招、社招等应隐藏。"
            "新闻、教程、研究、观点、政策解读等应保留。"
            "如果不确定，返回 maybe。"
            "只返回严格 JSON，不要输出多余文字。"
        )

        user_prompt = (
            "请按下面 JSON 格式返回："
            '{"decision":"keep|hide|maybe","category":"soft_ad|recruitment|promo|noise|unknown","confidence":0.0,"reason":"一句话说明原因"}\n'
            f"文章信息：{json.dumps(payload, ensure_ascii=False)}"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            decision = str(data.get("decision", "keep")).strip().lower()
            if decision not in {"keep", "hide", "maybe"}:
                decision = "keep"
            category = str(data.get("category", "unknown")).strip() or "unknown"
            try:
                confidence = float(data.get("confidence", 0.0))
            except (TypeError, ValueError):
                confidence = 0.0
            confidence = max(0.0, min(1.0, confidence))
            reason = str(data.get("reason", "")).strip() or "模型未返回原因"
            return ArticleFilterDecision(
                decision=decision,
                category=category,
                confidence=confidence,
                reason=reason,
                model_name=self.model,
            )
        except Exception as exc:
            logger.warning("文章 AI 过滤调用失败: %s", exc)
            return ArticleFilterDecision(
                decision="keep",
                category="unknown",
                confidence=0.0,
                reason=f"模型调用失败，已保留：{exc}",
                model_name=self.model,
            )


_engine: Optional[ArticleFilterEngine] = None


def get_article_filter_engine() -> ArticleFilterEngine:
    global _engine
    if _engine is None:
        _engine = ArticleFilterEngine()
    return _engine

