"""
按配置定期清理过期文章：删除或标记 article_tags、article_ai_filters 关联后处理 articles 表。
时间基准由 article.retention.basis 决定（created_at / publish_time）。
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from core.cache import clear_cache_pattern
from core.config import cfg
from core.models.article import Article
from core.models.article_ai_filter import ArticleAiFilter
from core.models.article_tags import ArticleTag
from core.models.base import DATA_STATUS
from core.print import print_info, print_warning


def _retention_cutoff() -> datetime:
    days = int(cfg.get("article.retention.days", 7) or 7)
    if days < 1:
        days = 1
    return datetime.now() - timedelta(days=days)


def _basis() -> str:
    b = (cfg.get("article.retention.basis", "created_at") or "created_at").strip().lower()
    if b in ("created_at", "publish_time"):
        return b
    print_warning(f"article.retention.basis 无效值 {b!r}，使用 created_at")
    return "created_at"


def _batch_size() -> int:
    n = int(cfg.get("article.retention.batch_size", 300) or 300)
    return max(50, min(n, 2000))


def _query_expired_ids(session, basis: str, cutoff: datetime, limit: int) -> List[str]:
    """返回一批待处理的文章 id（未删除）。"""
    q = session.query(Article.id).filter(Article.status != DATA_STATUS.DELETED)
    if basis == "created_at":
        q = q.filter(
            Article.created_at.isnot(None),
            Article.created_at < cutoff,
        )
    else:
        cutoff_ts = int(cutoff.timestamp())
        q = q.filter(
            Article.publish_time.isnot(None),
            Article.publish_time < cutoff_ts,
        )
    rows = q.limit(limit).all()
    return [str(r[0]) for r in rows]


def _delete_associations(session, ids: List[str]) -> None:
    if not ids:
        return
    session.query(ArticleTag).filter(ArticleTag.article_id.in_(ids)).delete(
        synchronize_session=False
    )
    session.query(ArticleAiFilter).filter(ArticleAiFilter.article_id.in_(ids)).delete(
        synchronize_session=False
    )


def purge_expired_articles() -> Dict[str, Any]:
    """
    执行一轮清理：按批删除直到没有候选记录。
    尊重 article.true_delete：True 为物理删除，False 为逻辑删除。
    """
    import core.db as db

    DB = db.Db(tag="文章存储周期清理")
    true_delete = bool(cfg.get("article.true_delete", True))
    basis = _basis()
    cutoff = _retention_cutoff()
    batch_limit = _batch_size()

    total_affected = 0
    batches = 0
    t0 = time.perf_counter()

    session = DB.get_session()
    try:
        while True:
            ids = _query_expired_ids(session, basis, cutoff, batch_limit)
            if not ids:
                break
            batches += 1
            _delete_associations(session, ids)
            if true_delete:
                session.query(Article).filter(Article.id.in_(ids)).delete(
                    synchronize_session=False
                )
            else:
                session.query(Article).filter(Article.id.in_(ids)).update(
                    {Article.status: DATA_STATUS.DELETED},
                    synchronize_session=False,
                )
            session.commit()
            total_affected += len(ids)
            print_info(
                f"文章存储周期清理：批次 {batches}，本批 {len(ids)} 篇"
                f"（{'物理删除' if true_delete else '逻辑删除'}），基准={basis}，截止早于 {cutoff.isoformat(timespec='seconds')}"
            )
    except Exception as e:
        session.rollback()
        print_warning(f"文章存储周期清理失败: {e}")
        raise
    finally:
        session.close()

    if total_affected > 0:
        clear_cache_pattern("articles:")
    elapsed = time.perf_counter() - t0
    print_info(
        f"文章存储周期清理完成：共 {batches} 批，处理 {total_affected} 篇，耗时 {elapsed:.2f}s"
    )
    return {
        "basis": basis,
        "cutoff": cutoff.isoformat(timespec="seconds"),
        "total": total_affected,
        "batches": batches,
        "true_delete": true_delete,
        "elapsed_seconds": round(elapsed, 3),
    }
