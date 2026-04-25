"""热点发现数据库操作模块"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from core.models.hot_topic_articles import HotTopicArticle
from core.models.hot_topic_runs import HotTopicRun
from core.models.hot_topics import HotTopic
from core.models.article import Article
from core.log import logger


def create_run(db: Session, window_days: int, model_name: str, prompt_version: str) -> HotTopicRun:
    """
    创建新的热点发现运行记录

    Args:
        db: 数据库会话
        window_days: 时间窗口（天数）
        model_name: LLM 模型名称
        prompt_version: Prompt 版本

    Returns:
        创建的 HotTopicRun 对象
    """
    run = HotTopicRun(
        id=str(uuid.uuid4()),
        window_days=window_days,
        status='pending',
        model_name=model_name,
        prompt_version=prompt_version,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def update_run_status(
    db: Session,
    run_id: str,
    status: str,
    article_count: Optional[int] = None,
    raw_request: Optional[str] = None,
    raw_response: Optional[str] = None,
    error_message: Optional[str] = None
) -> HotTopicRun:
    """
    更新运行记录状态

    Args:
        db: 数据库会话
        run_id: 运行记录 ID
        status: 新状态 (pending/running/success/failed)
        article_count: 文章数量
        raw_request: 原始请求
        raw_response: 原始响应
        error_message: 错误信息

    Returns:
        更新后的 HotTopicRun 对象
    """
    run = db.query(HotTopicRun).filter(HotTopicRun.id == run_id).first()
    if not run:
        raise ValueError(f"Run not found: {run_id}")

    run.status = status
    run.updated_at = datetime.now()

    if article_count is not None:
        run.article_count = article_count
    if raw_request is not None:
        run.raw_request = raw_request
    if raw_response is not None:
        run.raw_response = raw_response
    if error_message is not None:
        run.error_message = error_message

    db.commit()
    db.refresh(run)
    return run


def get_latest_successful_run(db: Session) -> Optional[HotTopicRun]:
    """
    获取最近一次成功运行的记录

    Args:
        db: 数据库会话

    Returns:
        HotTopicRun 对象，如果没有则返回 None
    """
    return db.query(HotTopicRun).filter(
        HotTopicRun.status == 'success'
    ).order_by(HotTopicRun.created_at.desc()).first()


def create_topics(db: Session, run_id: str, topics_data: List[Dict[str, Any]]) -> List[str]:
    """
    批量创建热点主题

    Args:
        db: 数据库会话
        run_id: 运行记录 ID
        topics_data: 主题数据列表，每个包含 topic_name, summary, signals, article_ids

    Returns:
        创建的 topic_id 列表
    """
    topic_ids = []
    for idx, topic_data in enumerate(topics_data):
        topic = HotTopic(
            id=str(uuid.uuid4()),
            run_id=run_id,
            topic_name=topic_data.get("topic_name", ""),
            summary=topic_data.get("summary", ""),
            signals_json=topic_data.get("signals", []),
            article_count=len(topic_data.get("article_ids", [])),
            sort_order=idx,
            created_at=datetime.now()
        )
        db.add(topic)
        topic_ids.append(topic.id)

    db.commit()
    return topic_ids


def create_topic_articles(db: Session, topic_id: str, article_ids: List[str]) -> int:
    """
    批量创建主题-文章关联

    Args:
        db: 数据库会话
        topic_id: 主题 ID
        article_ids: 文章 ID 列表

    Returns:
        创建的关联记录数量
    """
    for article_id in article_ids:
        relation = HotTopicArticle(
            id=str(uuid.uuid4()),
            topic_id=topic_id,
            article_id=article_id,
            created_at=datetime.now()
        )
        db.add(relation)

    db.commit()
    return len(article_ids)


def get_articles_by_ids(db: Session, article_ids: List[str]) -> List[Article]:
    """
    根据 ID 列表查询文章

    Args:
        db: 数据库会话
        article_ids: 文章 ID 列表

    Returns:
        文章对象列表
    """
    if not article_ids:
        return []
    return db.query(Article).filter(Article.id.in_(article_ids)).all()


def get_run_with_topics(db: Session, run_id: str) -> Optional[Dict[str, Any]]:
    """
    获取运行记录及其关联的主题

    Args:
        db: 数据库会话
        run_id: 运行记录 ID

    Returns:
        包含 run 和 topics 的字典，如果不存在则返回 None
    """
    run = db.query(HotTopicRun).filter(HotTopicRun.id == run_id).first()
    if not run:
        return None

    topics = db.query(HotTopic).filter(
        HotTopic.run_id == run_id
    ).order_by(HotTopic.sort_order.asc()).all()

    topics_data = []
    for topic in topics:
        article_refs = db.query(HotTopicArticle).filter(
            HotTopicArticle.topic_id == topic.id
        ).all()

        topics_data.append({
            "id": topic.id,
            "topic_name": topic.topic_name,
            "summary": topic.summary,
            "signals": topic.signals_json or [],
            "article_count": topic.article_count,
            "article_ids": [ref.article_id for ref in article_refs]
        })

    return {
        "run": run,
        "topics": topics_data
    }


def get_recent_articles_with_tags(
    db: Session,
    window_days: int = 3,
    limit: int = 500
) -> List[Dict[str, Any]]:
    """
    获取最近 N 天有标签的文章

    Args:
        db: 数据库会话
        window_days: 时间窗口（天数）
        limit: 最大文章数量

    Returns:
        文章列表，每个包含 id, title, tags
    """
    from sqlalchemy import and_
    from datetime import timedelta

    cutoff_time = datetime.now() - timedelta(days=window_days)
    cutoff_timestamp = int(cutoff_time.timestamp())

    # 查询最近发布的文章
    articles = db.query(Article).filter(
        and_(
            Article.publish_time >= cutoff_timestamp,
            Article.title.isnot(None),
            Article.title != "",
            Article.status == 1  # 假设 1 是正常状态
        )
    ).order_by(Article.publish_time.desc()).limit(limit).all()

    # 获取这些文章的标签
    from core.models.article_tags import ArticleTag
    from core.models.tags import Tags as TagsModel
    article_ids = [a.id for a in articles]

    if not article_ids:
        return []

    tag_refs = db.query(ArticleTag).filter(
        ArticleTag.article_id.in_(article_ids)
    ).all()

    # 获取所有标签 ID 并查询标签名
    tag_ids = list(set([ref.tag_id for ref in tag_refs]))
    tag_names = {}
    if tag_ids:
        tags = db.query(TagsModel).filter(TagsModel.id.in_(tag_ids)).all()
        tag_names = {t.id: t.name for t in tags if t.name}

    # 构建文章 -> 标签映射
    article_tags = {}
    for ref in tag_refs:
        if ref.article_id not in article_tags:
            article_tags[ref.article_id] = []
        # 使用标签名而不是 ID
        tag_name = tag_names.get(ref.tag_id, ref.tag_id)
        if tag_name:
            article_tags[ref.article_id].append(tag_name)

    # 组装结果
    result = []
    for article in articles:
        result.append({
            "id": article.id,
            "title": article.title,
            "tags": article_tags.get(article.id, [])
        })

    return result
