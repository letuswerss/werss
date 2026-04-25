"""标签提取模块 - 使用 AI（OpenAI 兼容 API）提取关键词"""
from typing import List, Optional
import os
from core.config import cfg
from core.log import logger
from core.print import print_error, print_success
from core.env_loader import load_dev_env_if_needed

DEFAULT_TAG_EXTRACT_PROMPT_TEMPLATE = """请从以下文章中提取 {{max_tags}} 个最核心的**具体**标签关键词。

【提取优先级（按重要性排序）】：
1. **公司名称**：文章中提到的所有公司、企业、组织名称（如：字节跳动、腾讯、阿里巴巴、OpenAI、Anthropic、英伟达、华为、小米等）
2. **产品/服务名称**：具体的产品、服务、平台名称（如：ChatGPT、Claude、豆包、微信、抖音、iOS、Android等）
3. **技术/工具名称**：具体的技术、框架、工具、协议名称（如：React、TensorFlow、Kubernetes、HTTP/3等）
4. **人物名称**：科技界、商业界的重要人物（如：马斯克、李彦宏、张一鸣等）
5. **特定事件/项目**：具体的项目、事件、活动名称（如：诺贝尔奖、登月计划等）
6. **特定领域/概念**：具体的细分领域或专业概念（如：自动驾驶、量子计算、区块链等）

【重要要求】：
1. **必须提取公司名称**：如果文章提到公司，公司名称必须包含在标签中
2. 标签词必须**具体且有区分度**，避免通用词汇
3. 避免提取：AI、大语言模型、云计算、机器学习、技术、产品等过于宽泛的词
4. 每个标签词 2-15 个字（公司名称可以更长）
5. 按重要性排序（公司名称通常最重要）
6. 只返回 JSON 数组格式，不要包含任何解释或思考过程

【好的示例】：
- 好："字节跳动"、"豆包视频"、"Seedance 1.5"、"火山引擎"、"Anthropic"、"Claude"、"诺贝尔奖"、"Crossplane"、"快手OneRec"、"李彦宏"、"DeepSeek"、"英伟达"、"NVIDIA"
- 差："AI"、"大语言模型"、"云计算"、"人工智能"、"技术"、"产品"、"公司"
{{custom_tags_hint}}

文章：
{{text}}

返回格式：["具体标签1", "具体标签2", "具体标签3"]"""

# 尝试导入 AI 相关模块（可选）
try:
    from openai import AsyncOpenAI
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger.warning("openai 模块未安装，AI 提取功能不可用")

# 全局单例实例，用于常驻内存
_global_extractor = None


class TagExtractor:
    """标签提取器，使用 AI（OpenAI 兼容 API）提取关键词"""

    def __init__(self):
        """初始化标签提取器"""
        self.ai_client = None
        self.ai_model = None
        self._custom_tags_cache = None  # 缓存用户自定义标签

        # 在开发环境中加载 .env 文件（如果存在）
        load_dev_env_if_needed()

        # 检查是否配置了 AI
        if AI_AVAILABLE:
            # 提供默认值 None，silent=True 避免输出警告（如果配置文件中没有这些项，会从环境变量读取）
            api_key_raw = cfg.get("openai.api_key", None, silent=True) or os.getenv("OPENAI_API_KEY", "")
            base_url_raw = cfg.get("openai.base_url", None, silent=True) or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            model_raw = cfg.get("openai.model", None, silent=True) or os.getenv("OPENAI_MODEL", "gpt-4o")

            # 确保类型为字符串
            api_key = str(api_key_raw) if api_key_raw else ""
            base_url = str(base_url_raw) if base_url_raw else "https://api.openai.com/v1"
            model = str(model_raw) if model_raw else "gpt-4o"

            if api_key:
                self.ai_client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                )
                self.ai_model = model
                logger.info(f"OpenAI API 已配置，模型: {model}, Base URL: {base_url}")
            else:
                logger.warning("OpenAI API Key 未配置，AI 提取功能不可用")
                logger.debug(f"检查路径: cfg.get('openai.api_key')={cfg.get('openai.api_key')}, os.getenv('OPENAI_API_KEY')={os.getenv('OPENAI_API_KEY', '')}")
        else:
            logger.warning("openai 模块未安装，AI 提取功能不可用")

    def _get_custom_tags(self) -> List[str]:
        """
        从数据库获取用户自定义的标签（用于标签提取时优先识别）

        Returns:
            用户自定义标签名称列表
        """
        if self._custom_tags_cache is not None:
            return self._custom_tags_cache

        try:
            from core.db import DB
            from core.models.tags import Tags

            session = DB.get_session()
            try:
                # 查询所有启用的用户自定义标签
                custom_tags = session.query(Tags).filter(
                    Tags.is_custom == True,
                    Tags.status == 1
                ).all()

                # 提取标签名称
                tag_names = [tag.name for tag in custom_tags if tag.name]

                # 缓存结果
                self._custom_tags_cache = tag_names

                if tag_names:
                    logger.debug(f"加载了 {len(tag_names)} 个用户自定义标签: {tag_names[:5]}...")

                return tag_names
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"获取用户自定义标签失败: {e}")
            # 如果查询失败，返回空列表，避免影响正常功能
            self._custom_tags_cache = []
            return []

    def refresh_custom_tags_cache(self):
        """刷新用户自定义标签缓存"""
        self._custom_tags_cache = None

    def _get_prompt_template(self) -> str:
        """获取可配置的标签提取提示词模板。"""
        try:
            template = cfg.get("article_tag.ai_prompt", None, silent=True)
            if template is None:
                return DEFAULT_TAG_EXTRACT_PROMPT_TEMPLATE
            template_str = str(template).strip()
            return template_str or DEFAULT_TAG_EXTRACT_PROMPT_TEMPLATE
        except Exception:
            return DEFAULT_TAG_EXTRACT_PROMPT_TEMPLATE

    def _html_to_text(self, html_content: str, to_markdown: bool = False) -> str:
        """
        将 HTML 内容转换为纯文本或 Markdown，用于关键词提取

        Args:
            html_content: HTML 内容
            to_markdown: 是否转换为 Markdown（True）还是纯文本（False）

        Returns:
            转换后的文本
        """
        if not html_content:
            return html_content

        # 检查是否包含 HTML 标签
        if '<' not in html_content or '>' not in html_content:
            return html_content

        try:
            from bs4 import BeautifulSoup
            import re

            # 解析 HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # 移除 script 和 style 标签及其内容（这些可能包含 CSS 样式和 JavaScript）
            for script in soup(["script", "style"]):
                script.decompose()

            # 移除所有元素的内联样式属性和 class 属性，避免提取到 CSS 样式信息
            from bs4 import Tag
            for tag in soup.find_all(True):
                # 类型检查：确保是 Tag 对象而不是 NavigableString
                if isinstance(tag, Tag):
                    if 'style' in tag.attrs:
                        del tag.attrs['style']
                    if 'class' in tag.attrs:
                        del tag.attrs['class']

            if to_markdown:
                # 转换为 Markdown
                try:
                    from markdownify import markdownify as md
                    # 先清理 HTML，移除不必要的标签
                    from bs4 import Tag
                    for tag in soup.find_all(['span', 'font']):
                        # 类型检查：确保是 Tag 对象而不是 NavigableString
                        if isinstance(tag, Tag):
                            tag.unwrap()
                    # 转换 HTML 到 Markdown
                    text = md(str(soup), heading_style="ATX", bullets='-*+')
                    # 清理多余的空白字符
                    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
                    text = re.sub(r'[ \t]+', ' ', text)
                    return text.strip()
                except ImportError:
                    logger.warning("markdownify 未安装，回退到纯文本提取")
                    to_markdown = False

            if not to_markdown:
                # 转换为纯文本
                text = soup.get_text(separator=' ', strip=True)
                # 清理多余的空白字符
                text = re.sub(r'\s+', ' ', text)
                # 过滤掉常见的字体名称（避免被提取为标签）
                font_names = ['Helvetica', 'Arial', 'Times New Roman', 'Courier New',
                             'Verdana', 'Georgia', 'Palatino', 'Garamond', 'Bookman',
                             'Comic Sans MS', 'Trebuchet MS', 'Impact', 'Lucida Console',
                             'Tahoma', 'Courier', 'Monaco', 'Menlo', 'Consolas',
                             'Roboto', 'Open Sans', 'Lato', 'Montserrat', 'Source Sans Pro']
                for font in font_names:
                    # 使用单词边界匹配，避免误删包含这些词的正常文本
                    text = re.sub(r'\b' + re.escape(font) + r'\b', '', text, flags=re.IGNORECASE)
                # 再次清理多余的空白字符
                text = re.sub(r'\s+', ' ', text).strip()
                return text

        except Exception as e:
            logger.warning(f"HTML 解析失败，使用原始内容: {e}")
            return html_content

    async def extract_with_ai(
        self,
        title: str,
        description: str = "",
        content: str = "",
        max_tags: int = 3
    ) -> List[str]:
        """
        使用 OpenAI API 提取标签关键词

        Args:
            title: 文章标题
            description: 文章描述
            content: 文章内容（可能是 HTML 格式）
            max_tags: 最大标签数量

        Returns:
            标签关键词列表
        """
        if not self.ai_client:
            logger.warning("OpenAI API 未配置，无法使用 AI 提取")
            return []

        # 处理 content 和 description
        if content:
            content = self._html_to_text(content)
        if description:
            description = self._html_to_text(description)

        # 构建输入文本
        text = f"标题：{title}\n"
        if description:
            text += f"描述：{description}\n"
        if content:
            # 截取前2000字符避免太长
            text += f"内容：{content[:2000]}"

        # 获取用户自定义标签，加入提示词中
        custom_tags = self._get_custom_tags()
        custom_tags_hint = ""
        if custom_tags:
            custom_tags_hint = f"\n\n【用户已有标签（优先匹配）】：{', '.join(custom_tags[:50])}"

        prompt_template = self._get_prompt_template()
        prompt = (
            prompt_template
            .replace("{{max_tags}}", str(max_tags))
            .replace("{{custom_tags_hint}}", custom_tags_hint)
            .replace("{{text}}", text)
        )

        try:
            import json

            # 检查是否是 Qwen3 模型，如果是则禁用思考功能
            # DeepSeek 模型不需要处理（不会有思考过程问题）
            model_name_lower = str(self.ai_model).lower() if self.ai_model else ""
            is_qwen3 = "qwen3" in model_name_lower or (
                "qwen" in model_name_lower and "3" in model_name_lower
            )

            # 构建 API 调用参数
            api_params = {
                "model": self.ai_model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的文章标签分析专家，用于热点主题聚类。必须优先提取公司名称、产品名称、技术名称等具体实体，避免宽泛的通用词汇。如果文章提到公司，公司名称必须包含在标签中。只返回 JSON 格式的标签数组，不要包含任何解释。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 300,  # 增加token限制，确保能提取更多标签
            }

            # 如果是 Qwen3 模型，添加禁用思考的参数
            if is_qwen3:
                api_params["extra_body"] = {
                    "chat_template_kwargs": {
                        "enable_thinking": False
                    }
                }

            response = await self.ai_client.chat.completions.create(**api_params)

            result = response.choices[0].message.content
            if result is None:
                logger.error("AI 返回内容为空")
                return []
            result = result.strip()

            # 处理可能包含 reasoning 标签的情况（如 o1 系列模型）
            import re
            original_result = result  # 保存原始结果用于错误日志

            # 移除各种 reasoning 标签及其内容（包括没有闭合标签的情况）
            reasoning_patterns = [
                r'<thinkstrip>.*?</thinkstrip>',
                r'<thinking>.*?</thinking>',
                r'<reasoning>.*?</reasoning>',
                r'<thinkstrip>.*?</thinkstrip>',
                # 处理没有闭合标签的情况（匹配到文件末尾或下一个标签）
                r'<thinkstrip>.*?(?=\[|$)',
                r'<thinking>.*?(?=\[|$)',
                r'<reasoning>.*?(?=\[|$)',
                r'<thinkstrip>.*?(?=\[|$)',
            ]
            for pattern in reasoning_patterns:
                result = re.sub(pattern, '', result, flags=re.DOTALL)
            result = result.strip()

            # 如果移除标签后结果为空，尝试从原始结果中提取 JSON
            if not result:
                result = original_result

            # 尝试直接解析 JSON
            try:
                tags = json.loads(result)
                if isinstance(tags, list):
                    cleaned_tags = [
                        tag.strip()
                        for tag in tags
                        if isinstance(tag, str) and tag.strip()
                    ]
                    if cleaned_tags:
                        return cleaned_tags[:max_tags]
                    logger.warning("AI 返回了空标签数组")
                    return []
            except json.JSONDecodeError:
                pass

            # 如果直接解析失败，尝试提取所有可能的 JSON 数组
            # 使用更宽松的正则表达式匹配 JSON 数组（包括嵌套和转义字符）
            json_array_pattern = r'\[(?:[^\[\]]+|\[[^\]]*\])*\]'
            matches = list(re.finditer(json_array_pattern, result, re.DOTALL))
            if not matches:
                # 如果没找到，尝试更简单的模式
                matches = list(re.finditer(r'\[.*?\]', result, re.DOTALL))

            if matches:
                # 从后往前尝试（通常最后的 JSON 是最终答案）
                for match in reversed(matches):
                    try:
                        candidate = match.group()
                        tags = json.loads(candidate)
                        if isinstance(tags, list) and len(tags) > 0:
                            # 验证标签格式：应该是字符串列表
                            if all(isinstance(tag, str) and len(tag.strip()) > 0 for tag in tags):
                                return tags[:max_tags]
                    except (json.JSONDecodeError, AttributeError):
                        continue

            # 如果还是失败，尝试查找包含引号的数组模式（更宽松）
            # 匹配类似 ["tag1", "tag2", "tag3"] 的模式
            quoted_array_pattern = r'\[(?:"[^"]*"(?:\s*,\s*"[^"]*")*)?\]'
            matches = list(re.finditer(quoted_array_pattern, result, re.DOTALL))
            if matches:
                for match in reversed(matches):
                    try:
                        tags = json.loads(match.group())
                        if isinstance(tags, list) and len(tags) > 0:
                            return tags[:max_tags]
                    except:
                        continue

            logger.error(f"AI 提取 JSON 解析失败，原始响应前500字符: {original_result[:500]}")
            return []
        except Exception as e:
            logger.error(f"AI 提取失败: {e}")
            return []

    def extract(
        self,
        title: str,
        description: str = "",
        content: str = "",
        method: str = "ai"
    ) -> List[str]:
        """
        统一接口，使用 AI 提取关键词（同步包装）

        Args:
            title: 文章标题
            description: 文章描述
            content: 文章内容（可能是 HTML 格式）
            method: 已废弃参数，保留兼容性

        Returns:
            标签关键词列表
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.extract_with_ai(
                            title,
                            description,
                            content,
                            int(cfg.get("article_tag.max_tags", 5))
                        )
                    )
                    return future.result()
            else:
                return asyncio.run(self.extract_with_ai(
                    title,
                    description,
                    content,
                    int(cfg.get("article_tag.max_tags", 5))
                ))
        except RuntimeError:
            return asyncio.run(self.extract_with_ai(
                title,
                description,
                content,
                int(cfg.get("article_tag.max_tags", 5))
            ))


def get_tag_extractor() -> TagExtractor:
    """
    获取全局单例的 TagExtractor 实例
    这样可以确保模型常驻内存，避免重复加载

    Returns:
        TagExtractor 实例（全局单例）
    """
    global _global_extractor
    if _global_extractor is None:
        _global_extractor = TagExtractor()

        if _global_extractor.ai_client is not None:
            logger.info("已创建全局 TagExtractor 实例，使用 AI 提取（OpenAI 兼容 API）")
        else:
            logger.warning(
                "已创建全局 TagExtractor 实例，但未检测到可用 API 客户端，"
                "AI 提取功能不可用"
            )
    else:
        # 如果实例已存在，但 AI 客户端未初始化，尝试重新初始化
        if AI_AVAILABLE and _global_extractor.ai_client is None:
            load_dev_env_if_needed()
            # 提供默认值 None，silent=True 避免输出警告（如果配置文件中没有这些项，会从环境变量读取）
            api_key_raw = cfg.get("openai.api_key", None, silent=True) or os.getenv("OPENAI_API_KEY", "")
            if api_key_raw:
                base_url_raw = cfg.get("openai.base_url", None, silent=True) or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
                model_raw = cfg.get("openai.model", None, silent=True) or os.getenv("OPENAI_MODEL", "gpt-4o")
                # 确保类型为字符串
                api_key = str(api_key_raw) if api_key_raw else ""
                base_url = str(base_url_raw) if base_url_raw else "https://api.openai.com/v1"
                model = str(model_raw) if model_raw else "gpt-4o"
                _global_extractor.ai_client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                )
                _global_extractor.ai_model = model
                logger.info(f"已重新初始化 OpenAI API 客户端，模型: {model}")
    return _global_extractor
