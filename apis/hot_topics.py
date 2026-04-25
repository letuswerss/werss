"""热点发现 API 路由"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.database import get_db
from core.models.base import DATA_STATUS
from core.models.feed import Feed
from core.models.hot_topic_runs import HotTopicRun
from core.models.hot_topics import HotTopic
from core.models.hot_topic_articles import HotTopicArticle
from core.models.article import Article
from .base import success_response, error_response

router = APIRouter(prefix="/hot-topics", tags=["热点发现"])


@router.get("/recent")
async def get_recent_hot_topics(
    db: Session = Depends(get_db),
):
    """
    获取最近一次成功的热点发现结果

    返回最新的热点主题列表，每个主题包含：
    - topic_id, topic_name, summary
    - signals (关键词)
    - article_count
    - article_ids (关联文章ID列表)
    """
    # 获取最近一次成功运行的记录
    run = db.query(HotTopicRun).filter(
        HotTopicRun.status == 'success'
    ).order_by(HotTopicRun.created_at.desc()).first()

    if not run:
        return success_response(data={
            "run_id": None,
            "window_days": 3,
            "topics": []
        })

    # 获取该次运行的所有主题
    topics = db.query(HotTopic).filter(
        HotTopic.run_id == run.id
    ).order_by(HotTopic.sort_order.asc(), HotTopic.article_count.desc()).all()

    result_topics = []
    for topic in topics:
        # 获取该主题关联的文章ID列表
        article_refs = db.query(HotTopicArticle).filter(
            HotTopicArticle.topic_id == topic.id
        ).all()

        article_ids = [ref.article_id for ref in article_refs]

        # 获取代表性文章标题（最多5篇）
        if article_ids:
            articles = db.query(Article).filter(
                Article.id.in_(article_ids)
            ).limit(5).all()
            representative_titles = [a.title for a in articles if a.title]
        else:
            representative_titles = []

        result_topics.append({
            "id": topic.id,
            "topic_name": topic.topic_name,
            "summary": topic.summary,
            "signals": topic.signals_json or [],
            "article_count": topic.article_count,
            "article_ids": article_ids,
            "representative_titles": representative_titles
        })

    return success_response(data={
        "run_id": run.id,
        "window_days": run.window_days,
        "model_name": run.model_name,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "topics": result_topics
    })


def _load_ordered_articles(
    db: Session, article_ids: List[str], limit: int
) -> List[Article]:
    """按关联表中的顺序取前 limit 篇未删除文章。"""
    picked = article_ids[:limit]
    if not picked:
        return []
    rows = (
        db.query(Article)
        .filter(
            Article.id.in_(picked),
            Article.status != DATA_STATUS.DELETED,
        )
        .all()
    )
    by_id: Dict[str, Article] = {a.id: a for a in rows}
    return [by_id[i] for i in picked if i in by_id]


def _mp_name_map(db: Session, mp_ids: List[Optional[str]]) -> Dict[str, str]:
    ids = [i for i in set(mp_ids) if i]
    if not ids:
        return {}
    feeds = db.query(Feed).filter(Feed.id.in_(ids)).all()
    return {f.id: (f.mp_name or "未知公众号") for f in feeds}


def _article_brief(
    a: Article,
    mp_name: str,
    include_content: bool,
    max_content_chars: Optional[int],
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "id": a.id,
        "title": a.title,
        "url": a.url,
        "description": a.description,
        "publish_time": a.publish_time,
        "mp_name": mp_name,
    }
    if include_content:
        text = a.content or ""
        if max_content_chars is not None and len(text) > max_content_chars:
            text = text[: max_content_chars] + "\n...[已截断]"
        out["content"] = text
    return out


@router.get("/skill-brief")
async def get_hot_topics_skill_brief(
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
    articles_per_topic: int = Query(3, ge=1, le=30, description="每个热点附带的参考文章篇数（默认 3，供撰写 Skill 使用）"),
    include_content: bool = Query(True, description="是否包含正文；false 时仅元数据，体积更小"),
    max_content_chars: Optional[int] = Query(
        None,
        description="单篇正文最大字符数，超出截断；不填则全文",
    ),
):
    """
    供外接「文章撰写 / 智能体」使用：在「最近一次成功热点 run」上，
    为**每个**热点取前 N 篇关联文章，带上标题、链接、公众号名与可选正文。

    需登录（`Authorization: Bearer`），与 `POST /hot-topics/rebuild` 相同。

    推荐配合服务端定时：先保证当日已跑过热点发现（定时任务或另行 rebuild），
    再本接口拉取 JSON，送给你的 Agent Skill 或流水线。
    """
    run = (
        db.query(HotTopicRun)
        .filter(HotTopicRun.status == "success")
        .order_by(HotTopicRun.created_at.desc())
        .first()
    )
    if not run:
        return success_response(
            data={
                "run_id": None,
                "window_days": 3,
                "model_name": None,
                "created_at": None,
                "articles_per_topic": articles_per_topic,
                "include_content": include_content,
                "topics": [],
            },
            message="暂无成功的热点发现结果",
        )

    topics = (
        db.query(HotTopic)
        .filter(HotTopic.run_id == run.id)
        .order_by(HotTopic.sort_order.asc(), HotTopic.article_count.desc())
        .all()
    )
    out_topics: List[Dict[str, Any]] = []

    for topic in topics:
        refs = (
            db.query(HotTopicArticle)
            .filter(HotTopicArticle.topic_id == topic.id)
            .all()
        )
        article_ids = [r.article_id for r in refs]
        arts = _load_ordered_articles(db, article_ids, articles_per_topic)
        mp_map = _mp_name_map(db, [a.mp_id for a in arts])
        reference_articles = [
            _article_brief(
                a,
                mp_map.get(a.mp_id, "未知公众号") if a.mp_id else "未知公众号",
                include_content,
                max_content_chars,
            )
            for a in arts
        ]
        out_topics.append(
            {
                "id": topic.id,
                "topic_name": topic.topic_name,
                "summary": topic.summary,
                "signals": topic.signals_json or [],
                "article_count": topic.article_count,
                "article_ids": article_ids,
                "reference_articles": reference_articles,
            }
        )

    return success_response(
        data={
            "run_id": run.id,
            "window_days": run.window_days,
            "model_name": run.model_name,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "articles_per_topic": articles_per_topic,
            "include_content": include_content,
            "topics": out_topics,
        }
    )


@router.post("/rebuild")
async def rebuild_hot_topics(
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
    window_days: int = Query(3, ge=1, le=30, description="时间窗口（天数）"),
    max_topics: int = Query(5, ge=3, le=20, description="最大热点数量"),
):
    """
    手动触发热点发现重建

    需要登录权限。参数：
    - window_days: 时间窗口（天数），默认 3 天
    - max_topics: 最大热点数量，默认 5

    触发后系统将：
    1. 拉取指定天数内的文章
    2. 调用 LLM 进行事件级聚类
    3. 存储新的热点结果

    注意：此操作可能需要较长时间，建议异步执行。
    """
    try:
        from core.hot_topics.service import run_discovery

        run_id, topic_count = await run_discovery(db, window_days=window_days, max_topics=max_topics)

        return success_response(data={
            "run_id": run_id,
            "topic_count": topic_count,
            "message": f"热点发现完成，共发现 {topic_count} 个主题"
        }, message="热点发现重建完成")

    except ImportError as e:
        return error_response(501, f"热点发现模块尚未实现: {str(e)}")
    except Exception as e:
        return error_response(500, f"热点发现失败: {str(e)}")


@router.get("/runs/{run_id}")
async def get_hot_topic_run(
    run_id: str,
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
):
    """
    获取指定 run 的详情

    需要登录权限。返回指定热点发现任务的完整信息。
    """
    run = db.query(HotTopicRun).filter(HotTopicRun.id == run_id).first()

    if not run:
        return error_response(404, "未找到指定的热点发现任务")

    # 获取该次运行的所有主题
    topics = db.query(HotTopic).filter(
        HotTopic.run_id == run.id
    ).order_by(HotTopic.sort_order.asc()).all()

    result_topics = []
    for topic in topics:
        article_refs = db.query(HotTopicArticle).filter(
            HotTopicArticle.topic_id == topic.id
        ).all()
        article_ids = [ref.article_id for ref in article_refs]

        # 获取文章详情
        articles = db.query(Article).filter(
            Article.id.in_(article_ids)
        ).all()
        article_details = []
        for art in articles:
            article_refs_detail = db.query(HotTopicArticle).filter(
                HotTopicArticle.article_id == art.id
            ).first()
            article_details.append({
                "id": art.id,
                "title": art.title,
                "publish_time": art.publish_time,
                "mp_id": art.mp_id
            })

        result_topics.append({
            "id": topic.id,
            "topic_name": topic.topic_name,
            "summary": topic.summary,
            "signals": topic.signals_json or [],
            "article_count": topic.article_count,
            "articles": article_details
        })

    return success_response(data={
        "id": run.id,
        "window_days": run.window_days,
        "article_count": run.article_count,
        "status": run.status,
        "model_name": run.model_name,
        "prompt_version": run.prompt_version,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "error_message": run.error_message,
        "topics": result_topics
    })
