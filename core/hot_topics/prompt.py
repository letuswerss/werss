"""热点发现 Prompt 模块"""
from typing import List, Dict, Any

PROMPT_VERSION = "hot_topics_v1"

# System Prompt
SYSTEM_PROMPT = """你是科技媒体热点分析助手。你的任务不是总结关键词，而是把文章按"同一事件 / 同一讨论主题"聚类。

核心规则：
1. 不要因为同属一家大公司就归为同一簇。
2. 同一公司下，不同事件必须拆开。
3. 只有在讨论的是同一事件、同一传闻、同一产品动态或同一争议时才合并。
4. 优先聚"事件"，不是聚"公司"。
5. 输出必须是严格 JSON 数组格式。"""

# User Prompt 模板
USER_PROMPT_TEMPLATE = """请将以下文章按"同一事件/同一讨论主题"归并为若干个热点簇。

【输出数量】：最多返回 {max_topics} 个热点，优先选择文章数量多、影响面广的主题。

【聚类规则】：
1. 不要因为同一家公司名字反复出现就归成同一簇。
2. 同一公司下，不同事件必须拆开。
3. 只有在文章讨论的是同一事件、同一传闻、同一产品动态、同一争议时才合并。
4. 优先聚"事件"，不是聚"公司"。
5. 若一篇文章无法明显归入任何簇，可以单独成簇。
6. 只输出最重要的 {max_topics} 个热点，不要输出所有可能的主题。

【应该合并的情况】：
- 多篇文章标题表达不同，但其实在讨论同一件新闻
- 多篇文章围绕同一个产品发布/爆料/争议
- 多篇文章对同一事件从不同角度报道

【不应该合并的情况】：
- 仅仅因为都提到了同一家大公司
- 同一家公司的不同产品线动态
- 同一标签词，但事件不一致

【输出格式】：
返回严格 JSON 数组，每个元素包含：
- topic_name: 事件型名称（不能只是单个公司名）
- summary: 一句话总结这个 topic
- signals: 核心信号词数组
- article_ids: 属于此簇的文章 id 数组（必须使用输入列表中的原始 id，不要修改格式）

示例格式：
[
  {{
    "topic_name": "Meta 强制采集员工输入训练 AI",
    "summary": "多篇文章围绕 Meta 收集员工交互数据训练 AI 的争议展开。",
    "signals": ["Meta", "员工数据收集", "鼠标键盘输入", "训练AI"],
    "article_ids": ["id_from_input_1", "id_from_input_2", "id_from_input_3"]
  }}
]

【文章列表】：
{article_cards}

请输出严格 JSON 数组，不要包含任何解释性文字。

重要：article_ids 必须直接使用上面文章列表中的 id 值，不要修改其格式。"""


def build_clustering_prompt(article_cards: List[Dict[str, Any]], max_topics: int = 5) -> str:
    """
    构建聚类 Prompt

    Args:
        article_cards: 文章卡片列表，每张卡片包含 id, title, tags
        max_topics: 最大热点数量，默认 5

    Returns:
        完整的 prompt 文本
    """
    # 格式化文章卡片
    formatted_cards = []
    for card in article_cards:
        tags_str = ", ".join(card.get("tags", []))
        formatted_cards.append(
            f'- id: {card["id"]}, title: {card["title"]}, tags: [{tags_str}]'
        )

    article_text = "\n".join(formatted_cards)

    return USER_PROMPT_TEMPLATE.format(article_cards=article_text, max_topics=max_topics)


def build_system_prompt() -> str:
    """获取 System Prompt"""
    return SYSTEM_PROMPT
