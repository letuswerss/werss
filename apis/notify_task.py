"""
推送任务（NotifyTask）API
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel

from core.auth import get_current_user
from core.db import DB
from core.models import NotifyTask
from core.print import print_error

from .base import error_response, success_response

router = APIRouter(prefix="/notify_tasks", tags=["推送任务"])


class NotifyTaskCreate(BaseModel):
    name: str = ""
    message_type: int = 0
    message_template: str = ""
    web_hook_url: str = ""
    mps_id: str = "[]"
    cron_exp: str = ""
    status: Optional[int] = 0


@router.get("", summary="获取推送任务列表")
async def list_notify_tasks(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    db = DB.get_session()
    try:
        db.expire_all()
        query = db.query(NotifyTask)
        if status is not None:
            query = query.filter(NotifyTask.status == status)
        total = query.count()
        rows = query.offset(offset).limit(limit).all()
        return success_response({
            "list": rows,
            "page": {"limit": limit, "offset": offset},
            "total": total,
        })
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.get("/{task_id}", summary="获取单个推送任务")
async def get_notify_task(task_id: str, current_user: dict = Depends(get_current_user)):
    db = DB.get_session()
    try:
        row = db.query(NotifyTask).filter(NotifyTask.id == task_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Notify task not found")
        return success_response(data=row)
    except HTTPException:
        raise
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.get("/{task_id}/run", summary="立即执行推送任务")
async def run_notify_task_api(task_id: str, current_user: dict = Depends(get_current_user)):
    try:
        from jobs.notify_task_job import run_notify_task
        tasks = run_notify_task(task_id)
        if not tasks:
            raise HTTPException(status_code=404, detail="Notify task not found or disabled")
        return success_response(data={"count": len(tasks)}, message="推送任务已加入队列")
    except HTTPException:
        raise
    except Exception as e:
        print_error(e)
        return error_response(code=402, message=str(e))


@router.post("", summary="创建推送任务", status_code=status.HTTP_201_CREATED)
async def create_notify_task(
    task_data: NotifyTaskCreate = Body(...),
    current_user: dict = Depends(get_current_user),
):
    db = DB.get_session()
    try:
        now = datetime.now()
        row = NotifyTask(
            id=str(uuid.uuid4()),
            name=task_data.name,
            message_type=task_data.message_type,
            message_template=task_data.message_template or "",
            web_hook_url=task_data.web_hook_url or "",
            mps_id=task_data.mps_id or "[]",
            cron_exp=task_data.cron_exp,
            status=task_data.status if task_data.status is not None else 0,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return success_response(data=row)
    except Exception as e:
        db.rollback()
        print_error(e)
        return error_response(code=500, message=str(e))


@router.put("/job/fresh", summary="重载推送任务")
async def reload_notify_jobs_api(current_user: dict = Depends(get_current_user)):
    try:
        from jobs.notify_task_job import reload_notify_jobs
        reload_notify_jobs()
        return success_response(message="推送任务已重载")
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.put("/{task_id}", summary="更新推送任务")
async def update_notify_task(
    task_id: str,
    task_data: NotifyTaskCreate = Body(...),
    current_user: dict = Depends(get_current_user),
):
    db = DB.get_session()
    try:
        row = db.query(NotifyTask).filter(NotifyTask.id == task_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Notify task not found")
        if task_data.name is not None:
            row.name = task_data.name
        if task_data.message_type is not None:
            row.message_type = task_data.message_type
        if task_data.message_template is not None:
            row.message_template = task_data.message_template
        if task_data.web_hook_url is not None:
            row.web_hook_url = task_data.web_hook_url
        if task_data.mps_id is not None:
            row.mps_id = task_data.mps_id
        if task_data.cron_exp is not None:
            row.cron_exp = task_data.cron_exp
        if task_data.status is not None:
            row.status = task_data.status
        row.updated_at = datetime.now()
        db.commit()
        db.refresh(row)
        return success_response(data=row)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))


@router.delete("/{task_id}", summary="删除推送任务")
async def delete_notify_task(task_id: str, current_user: dict = Depends(get_current_user)):
    db = DB.get_session()
    try:
        row = db.query(NotifyTask).filter(NotifyTask.id == task_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Notify task not found")
        db.delete(row)
        db.commit()
        return success_response(message="Notify task deleted")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))
