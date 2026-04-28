"""
抓取任务（FetchTask）API
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel

from core.auth import get_current_user
from core.db import DB
from core.models import FetchTask
from core.print import print_error

from .base import error_response, success_response

router = APIRouter(prefix="/fetch_tasks", tags=["抓取任务"])


def _reload_fetch_jobs_after_change():
    """DB 变更后同步 APScheduler；失败不回滚已提交数据，仅打日志。"""
    try:
        from jobs.fetch_task_job import reload_fetch_jobs

        reload_fetch_jobs()
    except Exception as e:
        print_error(f"抓取任务已保存但调度器重载失败: {e}")


class FetchTaskCreate(BaseModel):
    name: str = ""
    mps_id: str = "[]"
    cron_exp: str = ""
    max_page: Optional[int] = None
    status: Optional[int] = 0


@router.get("", summary="获取抓取任务列表")
async def list_fetch_tasks(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    db = DB.get_session()
    try:
        db.expire_all()
        query = db.query(FetchTask)
        if status is not None:
            query = query.filter(FetchTask.status == status)
        total = query.count()
        rows = query.offset(offset).limit(limit).all()
        return success_response({
            "list": rows,
            "page": {"limit": limit, "offset": offset},
            "total": total,
        })
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.get("/{task_id}", summary="获取单个抓取任务")
async def get_fetch_task(task_id: str, current_user: dict = Depends(get_current_user)):
    db = DB.get_session()
    try:
        row = db.query(FetchTask).filter(FetchTask.id == task_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Fetch task not found")
        return success_response(data=row)
    except HTTPException:
        raise
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.get("/{task_id}/run", summary="立即执行抓取任务")
async def run_fetch_task_api(task_id: str, current_user: dict = Depends(get_current_user)):
    try:
        from jobs.fetch_task_job import run_fetch_task
        tasks = run_fetch_task(task_id)
        if not tasks:
            raise HTTPException(status_code=404, detail="Fetch task not found or disabled")
        return success_response(data={"count": len(tasks)}, message="抓取任务已加入队列")
    except HTTPException:
        raise
    except Exception as e:
        print_error(e)
        return error_response(code=402, message=str(e))


@router.post("", summary="创建抓取任务", status_code=status.HTTP_201_CREATED)
async def create_fetch_task(
    task_data: FetchTaskCreate = Body(...),
    current_user: dict = Depends(get_current_user),
):
    db = DB.get_session()
    try:
        now = datetime.now()
        row = FetchTask(
            id=str(uuid.uuid4()),
            name=task_data.name,
            mps_id=task_data.mps_id or "[]",
            cron_exp=task_data.cron_exp,
            max_page=task_data.max_page,
            status=task_data.status if task_data.status is not None else 0,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        _reload_fetch_jobs_after_change()
        return success_response(data=row)
    except Exception as e:
        db.rollback()
        print_error(e)
        return error_response(code=500, message=str(e))


@router.put("/job/fresh", summary="重载抓取任务")
async def reload_fetch_jobs_api(current_user: dict = Depends(get_current_user)):
    try:
        from jobs.fetch_task_job import reload_fetch_jobs
        reload_fetch_jobs()
        return success_response(message="抓取任务已重载")
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.put("/{task_id}", summary="更新抓取任务")
async def update_fetch_task(
    task_id: str,
    task_data: FetchTaskCreate = Body(...),
    current_user: dict = Depends(get_current_user),
):
    db = DB.get_session()
    try:
        row = db.query(FetchTask).filter(FetchTask.id == task_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Fetch task not found")
        if task_data.name is not None:
            row.name = task_data.name
        if task_data.mps_id is not None:
            row.mps_id = task_data.mps_id
        if task_data.cron_exp is not None:
            row.cron_exp = task_data.cron_exp
        row.max_page = task_data.max_page
        if task_data.status is not None:
            row.status = task_data.status
        row.updated_at = datetime.now()
        db.commit()
        db.refresh(row)
        _reload_fetch_jobs_after_change()
        return success_response(data=row)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))


@router.delete("/{task_id}", summary="删除抓取任务")
async def delete_fetch_task(task_id: str, current_user: dict = Depends(get_current_user)):
    db = DB.get_session()
    try:
        row = db.query(FetchTask).filter(FetchTask.id == task_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Fetch task not found")
        db.delete(row)
        db.commit()
        _reload_fetch_jobs_after_change()
        return success_response(message="Fetch task deleted")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))
