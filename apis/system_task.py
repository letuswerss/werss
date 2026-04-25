"""系统级定时任务 API。

抓取/推送任务有独立数据表；文章清理、热点发现这类任务由配置驱动，
这里提供一个统一入口给前端任务管理页展示与操作。
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from core.auth import get_current_user
from core.config import cfg
from core.db import DB
from core.models import FetchTask, NotifyTask
from core.models.config_management import ConfigManagement

from .base import error_response, success_response

router = APIRouter(prefix="/system_tasks", tags=["系统定时任务"])


class ArticleRetentionUpdate(BaseModel):
    enabled: Optional[bool] = None
    cron: Optional[str] = Field(default=None, min_length=1, max_length=100)
    days: Optional[int] = Field(default=None, ge=1, le=9999)
    basis: Optional[str] = None


class HotTopicsScheduleUpdate(BaseModel):
    """热点发现定时任务：与 jobs/hot_topics_job 及手动重建共用 window_days / max_topics。"""

    enabled: Optional[bool] = None
    cron: Optional[str] = Field(default=None, min_length=1, max_length=100)
    window_days: Optional[int] = Field(default=None, ge=1, le=30)
    max_topics: Optional[int] = Field(default=None, ge=3, le=20)


def _config_bool(value: Any, default: bool = False) -> bool:
    if value is None or str(value).strip() == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _upsert_config(session, key: str, value: str, description: str) -> None:
    row = session.query(ConfigManagement).filter(ConfigManagement.config_key == key).first()
    if row:
        row.config_value = value
        row.description = description
    else:
        session.add(
            ConfigManagement(
                config_key=key,
                config_value=value,
                description=description,
            )
        )


def _invalidate_and_reload() -> None:
    try:
        from core.config_overrides import invalidate_config_overrides_cache

        invalidate_config_overrides_cache()
    except Exception:
        pass
    cfg.reload()


def _scheduler_job_map() -> Dict[str, Optional[str]]:
    try:
        from jobs.mps import scheduler

        status = scheduler.get_scheduler_status()
        return {job_id: next_run for job_id, next_run in status.get("next_run_times", [])}
    except Exception:
        return {}


def _earliest_next_run_by_job_prefix(scheduler, prefix: str) -> Optional[str]:
    """从 TaskScheduler 中取 job_id 以 prefix 开头、且最早的一次 next_run（ISO 时间字符串）。"""
    try:
        status = scheduler.get_scheduler_status()
        candidates: list[str] = []
        for job_id, next_run in status.get("next_run_times", []):
            if not next_run or not str(job_id).startswith(prefix):
                continue
            s = str(next_run).strip()
            if not s:
                continue
            if s.startswith("计算失败") or "未计划" in s:
                continue
            candidates.append(s)
        if not candidates:
            return None
        return min(candidates)
    except Exception:
        return None


def _fetch_tasks_aggregate_next_run() -> Optional[str]:
    """抓取任务注册在 jobs.fetch_task_job 的独立调度器上，与 mps.scheduler 无关。"""
    try:
        from jobs.fetch_task_job import scheduler as fetch_scheduler

        return _earliest_next_run_by_job_prefix(fetch_scheduler, "fetch_")
    except Exception:
        return None


def _notify_tasks_aggregate_next_run() -> Optional[str]:
    try:
        from jobs.notify_task_job import scheduler as notify_scheduler

        return _earliest_next_run_by_job_prefix(notify_scheduler, "notify_")
    except Exception:
        return None


def _system_task_payload() -> Dict[str, Any]:
    db = DB.get_session()
    try:
        job_map = _scheduler_job_map()
        fetch_next = _fetch_tasks_aggregate_next_run()
        notify_next = _notify_tasks_aggregate_next_run()
        fetch_enabled = db.query(FetchTask).filter(FetchTask.status == 1).count()
        notify_enabled = db.query(NotifyTask).filter(NotifyTask.status == 1).count()

        retention_enabled = _config_bool(cfg.get("article.retention.enabled", False), False)
        retention_cron = (cfg.get("article.retention.cron", "0 4 * * *") or "0 4 * * *").strip()
        retention_days = int(cfg.get("article.retention.days", 7) or 7)
        retention_basis = (cfg.get("article.retention.basis", "created_at") or "created_at").strip()

        hot_enabled = _config_bool(cfg.get("hot_topics.enabled", True), True)
        hot_cron = (cfg.get("hot_topics.cron", "0 9 * * *") or "0 9 * * *").strip()
        hot_window = int(cfg.get("hot_topics.window_days", 3) or 3)
        hot_window = max(1, min(hot_window, 30))
        hot_max = int(cfg.get("hot_topics.max_topics", 5) or 5)
        hot_max = max(3, min(hot_max, 20))

        return {
            "tasks": [
                {
                    "key": "fetch_tasks",
                    "name": "公众号抓取任务",
                    "type": "table",
                    "enabled": fetch_enabled > 0,
                    "summary": f"{fetch_enabled} 条启用中的抓取任务",
                    "cron": "按各抓取任务配置",
                    "next_run": fetch_next,
                    "manage_path": "/fetch-tasks",
                },
                {
                    "key": "notify_tasks",
                    "name": "消息推送任务",
                    "type": "table",
                    "enabled": notify_enabled > 0,
                    "summary": f"{notify_enabled} 条启用中的推送任务",
                    "cron": "按各推送任务配置",
                    "next_run": notify_next,
                    "manage_path": "/notify-tasks",
                },
                {
                    "key": "hot_topics",
                    "name": "热点发现",
                    "type": "config",
                    "enabled": hot_enabled,
                    "summary": f"分析最近 {hot_window} 天、最多 {hot_max} 个主题；需配置 LLM",
                    "cron": hot_cron,
                    "next_run": job_map.get("hot_topics_discovery"),
                    "manage_path": "/system-tasks#hot-topics",
                },
                {
                    "key": "article_retention",
                    "name": "文章定期清理",
                    "type": "config",
                    "enabled": retention_enabled,
                    "summary": f"保留最近 {retention_days} 天，基准：{retention_basis}",
                    "cron": retention_cron,
                    "next_run": job_map.get("werss_article_retention"),
                    "manage_path": "/system-tasks#article-retention",
                },
            ],
            "hot_topics": {
                "enabled": hot_enabled,
                "cron": hot_cron,
                "window_days": hot_window,
                "max_topics": hot_max,
                "next_run": job_map.get("hot_topics_discovery"),
            },
            "article_retention": {
                "enabled": retention_enabled,
                "cron": retention_cron,
                "days": max(1, min(retention_days, 9999)),
                "basis": retention_basis if retention_basis in ("created_at", "publish_time") else "created_at",
                "next_run": job_map.get("werss_article_retention"),
            },
        }
    finally:
        db.close()


@router.get("", summary="获取系统定时任务概览")
async def list_system_tasks(current_user: dict = Depends(get_current_user)):
    try:
        return success_response(data=_system_task_payload())
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.put("/article-retention", summary="更新文章定期清理任务配置")
async def update_article_retention(
    data: ArticleRetentionUpdate = Body(...),
    current_user: dict = Depends(get_current_user),
):
    db = DB.get_session()
    try:
        if data.basis is not None and data.basis not in ("created_at", "publish_time"):
            raise HTTPException(status_code=400, detail="basis must be created_at or publish_time")

        if data.enabled is not None:
            _upsert_config(
                db,
                "article.retention.enabled",
                "true" if data.enabled else "false",
                "是否启用按保留天数定期清理旧文章",
            )
        if data.cron is not None:
            _upsert_config(
                db,
                "article.retention.cron",
                data.cron.strip(),
                "文章定期清理 cron 表达式",
            )
        if data.days is not None:
            _upsert_config(
                db,
                "article.retention.days",
                str(data.days),
                "文章保留最近多少天（按时间基准与当前时间比较）",
            )
        if data.basis is not None:
            _upsert_config(
                db,
                "article.retention.basis",
                data.basis,
                "清理时间基准：created_at=入库时间，publish_time=微信发布时间",
            )

        db.commit()
        _invalidate_and_reload()

        from jobs.mps import reload_job

        reload_job()
        return success_response(data=_system_task_payload(), message="文章定期清理任务已保存并重载")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))
    finally:
        db.close()


@router.post("/article-retention/run", summary="立即执行一次文章定期清理")
async def run_article_retention(current_user: dict = Depends(get_current_user)):
    try:
        from core.article_retention import purge_expired_articles

        result = purge_expired_articles()
        return success_response(data=result, message="文章定期清理已执行")
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.put("/reload", summary="重载全部定时任务")
async def reload_system_tasks(current_user: dict = Depends(get_current_user)):
    try:
        _invalidate_and_reload()
        from jobs.mps import reload_job

        reload_job()
        return success_response(data=_system_task_payload(), message="全部定时任务已重载")
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.put("/hot-topics", summary="更新热点发现定时任务配置")
async def update_hot_topics_schedule(
    data: HotTopicsScheduleUpdate = Body(...),
    current_user: dict = Depends(get_current_user),
):
    if (
        data.enabled is None
        and data.cron is None
        and data.window_days is None
        and data.max_topics is None
    ):
        raise HTTPException(
            status_code=400, detail="至少需要提供 enabled、cron、window_days、max_topics 中的一项",
        )

    db = DB.get_session()
    try:
        if data.enabled is not None:
            _upsert_config(
                db,
                "hot_topics.enabled",
                "true" if data.enabled else "false",
                "是否启用热点发现定时任务",
            )
        if data.cron is not None:
            _upsert_config(
                db,
                "hot_topics.cron",
                data.cron.strip(),
                "热点发现 cron 表达式（分 时 日 月 周）",
            )
        if data.window_days is not None:
            _upsert_config(
                db,
                "hot_topics.window_days",
                str(data.window_days),
                "热点分析时间窗口（天）",
            )
        if data.max_topics is not None:
            _upsert_config(
                db,
                "hot_topics.max_topics",
                str(data.max_topics),
                "热点发现最大主题数量",
            )

        db.commit()
        _invalidate_and_reload()

        from jobs.mps import reload_job

        reload_job()
        return success_response(data=_system_task_payload(), message="热点发现任务已保存并重载")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))
    finally:
        db.close()


@router.delete("/hot-topics", summary="关闭热点发现定时任务（不删历史数据）")
async def delete_hot_topics_schedule(current_user: dict = Depends(get_current_user)):
    """相当于将 hot_topics.enabled 设为 false 并重载调度器。"""
    return await update_hot_topics_schedule(
        HotTopicsScheduleUpdate(enabled=False), current_user
    )


@router.post("/hot-topics/run", summary="按当前配置立即执行一次热点发现")
async def run_hot_topics_now(current_user: dict = Depends(get_current_user)):
    from core.database import get_db
    from core.hot_topics.service import run_discovery_sync

    _invalidate_and_reload()
    wd = int(cfg.get("hot_topics.window_days", 3) or 3)
    mt = int(cfg.get("hot_topics.max_topics", 5) or 5)
    wd = max(1, min(wd, 30))
    mt = max(3, min(mt, 20))
    db = get_db()
    try:
        run_id, topic_count = run_discovery_sync(db, window_days=wd, max_topics=mt)
        return success_response(
            data={"run_id": run_id, "topic_count": topic_count},
            message="热点发现已执行",
        )
    except Exception as e:
        return error_response(code=500, message=str(e))
    finally:
        db.close()
