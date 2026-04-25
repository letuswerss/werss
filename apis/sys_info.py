import platform
import time
import sys
import psutil
from fastapi import APIRouter,Depends
from typing import Dict, Any
from core.auth import get_current_user
from .base import success_response, error_response
from driver.token import wx_cfg
from core.config import cfg
from jobs.mps import TaskQueue
from driver.success import getLoginInfo,getStatus
from jobs.mps import scheduler as mps_scheduler
from jobs.taskmsg import get_message_task
from jobs.fetch_no_article import scheduler as fetch_scheduler
router = APIRouter(prefix="/sys", tags=["系统信息"])

# 记录服务器启动时间
_START_TIME = time.time()

@router.get("/version", summary="版本信息（健康检查）")
async def get_version() -> Dict[str, Any]:
    """获取版本信息，用于健康检查"""
    try:
        from .ver import API_VERSION
        from core.config import VERSION as CORE_VERSION
        return success_response(data={
            'api_version': API_VERSION,
            'core_version': CORE_VERSION,
            'status': 'running'
        })
    except Exception as e:
        return error_response(
            code=50001,
            message=f"获取版本信息失败: {str(e)}"
        )

@router.get("/base_info", summary="常规信息")
async def get_base_info() -> Dict[str, Any]:
    try:
        from .ver import API_VERSION
        from core.config import VERSION as CORE_VERSION,LATEST_VERSION
        base_info = {
            'api_version': API_VERSION,
            'core_version': CORE_VERSION,
            "ui":{
                "name": cfg.get("server.name",""),
                "web_name": cfg.get("server.web_name","WeRss公众号订阅平台"),
            }
        }
        return success_response(data=base_info)
    except Exception as e:
        return error_response(
            code=50001,
            message=f"获取信息失败: {str(e)}"
        )    
    

from core.resource import get_system_resources
@router.get("/resources", summary="获取系统资源使用情况")
async def system_resources(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取系统资源使用情况
    
    Returns:
        BaseResponse格式的资源使用信息，包括:
        - cpu: CPU使用率(%)
        - memory: 内存使用情况
        - disk: 磁盘使用情况
    """
    try:
        resources_info=get_system_resources()
        resources_info["queue"]=TaskQueue.get_queue_info(),
        return success_response(data=resources_info)
    except Exception as e:
        return error_response(
            code=50002,
            message=f"获取系统资源失败: {str(e)}"
        )
from core.article_lax import ARTICLE_INFO,laxArticle
from .ver import API_VERSION
from core.base import VERSION as CORE_VERSION,LATEST_VERSION
@router.get("/info", summary="获取系统信息")
async def get_system_info(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前系统的各种信息
    
    Returns:
        BaseResponse格式的系统信息，包括:
        - os: 操作系统信息
        - python_version: Python版本
        - uptime: 服务器运行时间(秒)
        - system: 系统详细信息
    """
    try:
      
        wx_cfg.reload()
        # 获取系统信息
        system_info = {
            'os': {
                'name': platform.system(),
                'version': platform.version(),
                'release': platform.release(),
            },
            'python_version': sys.version,
            'uptime': round(time.time() - _START_TIME, 2),
            'system': {
                'node': platform.node(),
                'machine': platform.machine(),
                'processor': platform.processor(),
            },
            'api_version': API_VERSION,
            'core_version': CORE_VERSION,
            'latest_version':LATEST_VERSION,
            'need_update':CORE_VERSION != LATEST_VERSION,
            "wx":{
                'token':wx_cfg.get('token',''),
                'expiry_time':wx_cfg.get('expiry.expiry_time','') if getStatus() else "",
                "info":getLoginInfo(),
                "login":getStatus(),
            },
            "article":ARTICLE_INFO,
            'queue':TaskQueue.get_queue_info(),
            "scheduler": {
                "mps": mps_scheduler.get_scheduler_status() if hasattr(mps_scheduler, 'get_scheduler_status') else {"running": False, "job_count": 0, "next_run_times": []},
                "fetch": fetch_scheduler.get_scheduler_status() if hasattr(fetch_scheduler, 'get_scheduler_status') else {"running": False, "job_count": 0, "next_run_times": []},
            },
            "message_tasks": [{
                "id": task.id,
                "name": task.name,
                "cron_exp": task.cron_exp,
                "status": task.status,
                "mps_id": task.mps_id
            } for task in (get_message_task() or [])],
        }
        return success_response(data=system_info)
    except Exception as e:
        return error_response(
            code=50001,
            message=f"获取系统信息失败: {str(e)}"
        )