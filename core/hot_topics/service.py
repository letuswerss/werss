"""热点发现核心服务模块"""
import asyncio
import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from core.config import cfg
from core.log import logger
from core.print import print_info, print_error, print_success
from .prompt import build_clustering_prompt, build_system_prompt, PROMPT_VERSION
from .parser import parse_llm_response, ParseError
from .repository import (
    create_run,
    update_run_status,
    create_topics,
    create_topic_articles,
    get_recent_articles_with_tags,
)


async def fetch_recent_articles(db: Session, window_days: int = 3, limit: int = 200) -> List[Dict[str, Any]]:
    """
    拉取最近 N 天的文章

    Args:
        db: 数据库会话
        window_days: 时间窗口（天数）
        limit: 最大文章数量

    Returns:
        文章列表，每个包含 id, title, tags
    """
    from .repository import get_recent_articles_with_tags
    return get_recent_articles_with_tags(db, window_days=window_days, limit=limit)


def build_article_cards(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    构造文章卡片用于 LLM 输入

    Args:
        articles: 文章列表

    Returns:
        文章卡片列表
    """
    cards = []
    for article in articles:
        cards.append({
            "id": article["id"],
            "title": article["title"],
            "tags": article.get("tags", [])
        })
    return cards


async def call_llm_clustering(
    cards: List[Dict[str, Any]],
    api_key: str,
    base_url: str,
    model: str,
    max_topics: int = 5
) -> str:
    """
    调用 LLM 进行聚类

    Args:
        cards: 文章卡片列表
        api_key: OpenAI API Key
        base_url: API Base URL
        model: 模型名称
        max_topics: 最大热点数量

    Returns:
        LLM 返回的原始 JSON 字符串
    """
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    system_prompt = build_system_prompt()
    user_prompt = build_clustering_prompt(cards, max_topics=max_topics)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=8000,
        )

        result = response.choices[0].message.content
        if result is None:
            raise ValueError("LLM 返回内容为空")

        return result.strip()

    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        raise


def validate_and_parse(response_text: str, valid_article_ids: List[str]) -> List[Dict[str, Any]]:
    """
    校验并解析 LLM 响应

    Args:
        response_text: LLM 返回的原始文本
        valid_article_ids: 有效的文章 ID 列表

    Returns:
        解析后的 topics 数组

    Raises:
        ParseError: 当解析失败时
    """
    topics, errors = parse_llm_response(response_text, valid_article_ids)

    if errors:
        logger.warning(f"解析发现 {len(errors)} 个问题")

    return topics


async def save_results(
    db: Session,
    run_id: str,
    topics_data: List[Dict[str, Any]]
) -> int:
    """
    保存聚类结果到数据库

    Args:
        db: 数据库会话
        run_id: 运行记录 ID
        topics_data: topics 数据

    Returns:
        创建的 topic 数量
    """
    # 创建 topics
    topic_ids = create_topics(db, run_id, topics_data)

    # 创建 topic-article 关联
    for topic_id, topic_data in zip(topic_ids, topics_data):
        create_topic_articles(db, topic_id, topic_data.get("article_ids", []))

    return len(topic_ids)


async def run_discovery(db: Session, window_days: int = 3, max_topics: int = 5) -> tuple[str, int]:
    """
    执行热点发现主流程

    Args:
        db: 数据库会话
        window_days: 时间窗口（天数）
        max_topics: 最大热点数量

    Returns:
        (run_id, topic_count)

    Raises:
        Exception: 当执行失败时
    """
    # 1. 获取配置
    api_key = cfg.get("openai.api_key", None) or os.getenv("OPENAI_API_KEY", "")
    base_url = cfg.get("openai.base_url", None) or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = cfg.get("openai.model", None) or os.getenv("OPENAI_MODEL", "gpt-4o")

    if not api_key:
        raise ValueError("OpenAI API Key 未配置")

    # 2. 创建 run 记录
    run = create_run(db, window_days, model, PROMPT_VERSION)

    try:
        # 3. 更新状态为 running
        update_run_status(db, run.id, "running")

        print_info(f"开始热点发现 (run_id={run.id}, window_days={window_days}, max_topics={max_topics})")

        # 4. 拉取文章
        articles = await fetch_recent_articles(db, window_days)
        print_info(f"拉取到 {len(articles)} 篇文章")

        if not articles:
            update_run_status(db, run.id, "success", article_count=0)
            return run.id, 0

        # 5. 构建文章卡片
        cards = build_article_cards(articles)
        valid_article_ids = [c["id"] for c in cards]

        # 6. 调用 LLM
        print_info("调用 LLM 进行聚类...")
        raw_response = await call_llm_clustering(cards, api_key, base_url, model, max_topics)

        # 7. 解析响应
        topics_data, parse_errors = parse_llm_response(raw_response, valid_article_ids)

        if parse_errors:
            logger.warning(f"解析发现 {len(parse_errors)} 个问题，已跳过无效主题")

        print_info(f"LLM 返回 {len(topics_data)} 个热点主题")

        # 8. 保存结果
        topic_count = await save_results(db, run.id, topics_data)

        # 9. 更新状态为 success
        update_run_status(
            db, run.id, "success",
            article_count=len(articles),
            raw_response=raw_response[:50000]
        )

        print_success(f"热点发现完成！发现 {topic_count} 个主题")

        return run.id, topic_count

    except ParseError as e:
        error_msg = f"LLM 响应解析失败: {str(e)}"
        print_error(error_msg)
        # 尝试记录已有的 raw_response（在变量作用域内可能不存在）
        try:
            update_run_status(
                db, run.id, "failed",
                error_message=error_msg,
                raw_request=raw_request[:10000] if 'raw_request' in dir() else None,
                raw_response=raw_response[:50000] if 'raw_response' in dir() else None
            )
        except:
            update_run_status(db, run.id, "failed", error_message=error_msg)
        raise

    except Exception as e:
        error_msg = f"热点发现失败: {str(e)}"
        print_error(error_msg)
        # 尝试记录已有的数据
        try:
            update_run_status(
                db, run.id, "failed",
                error_message=error_msg,
                raw_request=raw_request[:10000] if 'raw_request' in dir() else None,
                raw_response=raw_response[:50000] if 'raw_response' in dir() else None
            )
        except:
            update_run_status(db, run.id, "failed", error_message=error_msg)
        raise


# 同步包装函数（用于非异步环境）
def run_discovery_sync(db: Session, window_days: int = 3, max_topics: int = 5) -> tuple[str, int]:
    """
    同步包装的热点发现函数

    Args:
        db: 数据库会话
        window_days: 时间窗口（天数）
        max_topics: 最大热点数量

    Returns:
        (run_id, topic_count)
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, run_discovery(db, window_days, max_topics))
                return future.result()
        else:
            return asyncio.run(run_discovery(db, window_days, max_topics))
    except RuntimeError:
        return asyncio.run(run_discovery(db, window_days, max_topics))
