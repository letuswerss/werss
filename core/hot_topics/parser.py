"""热点发现 LLM 输出解析模块"""
import json
import re
from typing import List, Dict, Any, Tuple
from core.log import logger


class ParseError(Exception):
    """解析错误"""
    pass


def parse_llm_response(response_text: str, valid_article_ids: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    解析 LLM 返回的 JSON 响应

    Args:
        response_text: LLM 返回的原始文本
        valid_article_ids: 有效的文章 ID 列表

    Returns:
        (topics 数组, 错误信息列表)

    Raises:
        ParseError: 当解析失败时
    """
    errors = []
    valid_id_set = set(valid_article_ids)

    # 1. 清理响应文本，移除可能的 reasoning 标签
    cleaned_text = _clean_reasoning_tags(response_text)

    # 2. 尝试解析 JSON
    try:
        data = _extract_json_array(cleaned_text)
    except json.JSONDecodeError as e:
        raise ParseError(f"JSON 解析失败: {str(e)}")

    # 3. 校验顶层是数组
    if not isinstance(data, list):
        raise ParseError(f"顶层必须是数组，实际类型: {type(data).__name__}")

    # 4. 校验每个 topic
    validated_topics = []
    used_article_ids = set()

    for idx, topic in enumerate(data):
        topic_errors = []

        # 校验字段完整性
        if not isinstance(topic, dict):
            topic_errors.append(f"第 {idx+1} 个元素不是对象")
            continue

        # 检查必需字段
        topic_name = topic.get("topic_name", "")
        summary = topic.get("summary", "")
        signals = topic.get("signals", [])
        article_ids = topic.get("article_ids", [])

        if not topic_name or not isinstance(topic_name, str):
            topic_errors.append(f"topic_name 缺失或类型错误")
        if not summary or not isinstance(summary, str):
            topic_errors.append(f"summary 缺失或类型错误")
        if not isinstance(signals, list):
            topic_errors.append(f"signals 必须是数组")
        if not isinstance(article_ids, list):
            topic_errors.append(f"article_ids 必须是数组")

        if topic_errors:
            errors.extend([f"Topic {idx+1}: {e}" for e in topic_errors])
            continue

        # 校验 article_ids
        invalid_ids = [aid for aid in article_ids if aid not in valid_id_set]

        if invalid_ids:
            errors.append(f"Topic {idx+1} ({topic_name}): 包含无效 article_ids: {invalid_ids}")
            # 移除无效 ID
            article_ids = [aid for aid in article_ids if aid in valid_id_set]

        # 检查文章是否已被使用
        duplicate_ids = [aid for aid in article_ids if aid in used_article_ids]
        if duplicate_ids:
            errors.append(f"Topic {idx+1} ({topic_name}): 文章 ID 已被其他 topic 使用: {duplicate_ids}")
            # 移除重复 ID
            article_ids = [aid for aid in article_ids if aid not in used_article_ids]

        # 更新已使用 ID 集合
        used_article_ids.update(article_ids)

        # 如果没有文章了，跳过这个 topic
        if not article_ids:
            errors.append(f"Topic {idx+1} ({topic_name}): 没有有效的文章关联，已跳过")
            continue

        # 清理数据
        cleaned_signals = _clean_string_list(signals)
        cleaned_article_ids = _clean_string_list(article_ids)

        # 构建验证后的 topic
        validated_topics.append({
            "topic_name": topic_name.strip(),
            "summary": summary.strip(),
            "signals": cleaned_signals,
            "article_ids": cleaned_article_ids
        })

    if errors:
        logger.warning(f"解析 LLM 响应时发现 {len(errors)} 个问题: {errors[:5]}")

    return validated_topics, errors


def _clean_reasoning_tags(text: str) -> str:
    """移除可能的 reasoning 标签及其内容"""
    patterns = [
        r'<thinkstrip>.*?</thinkstrip>',
        r'<thinking>.*?</thinking>',
        r'<reasoning>.*?</reasoning>',
        r'```json\s*\n',
        r'```\s*$',
        r'<think>.*?</think>',
    ]
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
    return cleaned.strip()


def _extract_json_array(text: str) -> Any:
    """从文本中提取 JSON 数组"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 JSON 数组（从后往前，最后的通常是最终答案）
    json_pattern = r'\[\s*\{.*?\}\s*\]'
    matches = list(re.finditer(json_pattern, text, re.DOTALL))

    for match in reversed(matches):
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            continue

    # 最后尝试宽松的模式
    loose_pattern = r'\[.*?\]'
    matches = list(re.finditer(loose_pattern, text, re.DOTALL))
    for match in reversed(matches):
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            continue

    raise json.JSONDecodeError("无法从响应中提取有效的 JSON 数组", text, 0)


def _clean_string_list(items: List[Any]) -> List[str]:
    """清理字符串列表：去重、移除空值、确保字符串类型"""
    if not items:
        return []

    result = set()
    for item in items:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                result.add(cleaned)

    return sorted(result)


def validate_topic_count(topics: List[Dict[str, Any]], min_count: int = 3, max_count: int = 10) -> Tuple[bool, str]:
    """
    验证 topic 数量是否合理

    Returns:
        (是否合理, 说明文字)
    """
    count = len(topics)

    if count < min_count:
        return False, f"Topic 数量过少: {count}，建议至少 {min_count} 个"

    if count > max_count:
        return False, f"Topic 数量过多: {count}，建议不超过 {max_count} 个"

    return True, f"Topic 数量合理: {count}"
