"""
抓取任务（FetchTask）调度

只做一件事：按 cron 拉取指定公众号的最新文章，写入 DB。
"""
import json
from typing import List, Union, Optional

import core.db as db
from core.config import cfg
from core.log import logger
from core.models import FetchTask
from core.models.feed import Feed
from core.print import print_error, print_info, print_success, print_warning
from core.queue import TaskQueue
from core.task import TaskScheduler
from core.wx import WxGather

from .article import UpdateArticle, Update_Over

interval = int(cfg.get("interval", 60))
_db = db.Db(tag="抓取任务")
scheduler = TaskScheduler()


def _check_session_valid() -> bool:
    """复用 mps.py 中的 session 校验逻辑（避免重复实现）"""
    from .mps import check_session_valid
    return check_session_valid()


def get_active_fetch_tasks(task_id: Union[str, list, None] = None) -> Optional[List[FetchTask]]:
    """获取启用中的抓取任务"""
    try:
        session = db.DB.get_session()
        session.expire_all()
        query = session.query(FetchTask).filter(FetchTask.status == 1)
        if task_id:
            if isinstance(task_id, list):
                query = query.filter(FetchTask.id.in_(task_id))
            else:
                query = query.filter(FetchTask.id == task_id)
        tasks = query.all()
        return tasks if tasks else None
    except Exception as e:
        logger.error(f"获取抓取任务失败: {e}")
        return None


def get_feeds_for_task(task: FetchTask) -> List[Feed]:
    """根据抓取任务返回需要处理的公众号；mps_id 为空时返回全部"""
    try:
        mps = json.loads(task.mps_id) if task.mps_id else []
    except Exception:
        mps = []

    if not mps:
        return _db.get_all_mps()
    ids = ",".join([item["id"] for item in mps if isinstance(item, dict) and "id" in item])
    feeds = _db.get_mps_list(ids) if ids else []
    return feeds if feeds else _db.get_all_mps()


def fetch_one_feed(feed: Feed, max_pages: int) -> int:
    """抓取单个公众号的最新文章并写库；返回新增数量"""
    wx = WxGather().Model()
    try:
        wx.get_Articles(
            feed.faker_id,
            CallBack=UpdateArticle,
            Mps_id=feed.id,
            Mps_title=feed.mp_name,
            MaxPage=max_pages,
            Over_CallBack=Update_Over,
            interval=interval,
        )
        return wx.all_count()
    except Exception as e:
        print_error(f"抓取 {feed.mp_name} 失败: {e}")
        return 0


def do_fetch_task(task: FetchTask):
    """执行一条抓取任务"""
    if not _check_session_valid():
        return

    feeds = get_feeds_for_task(task)
    if not feeds:
        print_warning(f"抓取任务[{task.name}]没有可处理的公众号")
        return

    max_pages = int(task.max_page) if task.max_page else int(cfg.get("max_page", 1))
    print_info(f"【抓取任务】{task.name}：开始抓取 {len(feeds)} 个公众号，每个 {max_pages} 页")

    total = 0
    for feed in feeds:
        count = fetch_one_feed(feed, max_pages)
        total += count
    print_success(f"【抓取任务】{task.name} 完成，共更新 {total} 条")


def add_fetch_to_queue(task: FetchTask):
    """把抓取任务塞进任务队列（按队列顺序串行执行）"""
    TaskQueue.add_task(do_fetch_task, task)
    print_info(f"【抓取任务】{task.name} 已入队列")


def start_fetch_jobs(task_id: Union[str, list, None] = None):
    """注册所有启用的抓取任务到调度器"""
    tasks = get_active_fetch_tasks(task_id)
    if not tasks:
        print_info("没有启用的抓取任务")
        return

    for task in tasks:
        if not task.cron_exp:
            print_error(f"抓取任务[{task.id}]没有设置 cron 表达式")
            continue
        scheduler.add_cron_job(
            add_fetch_to_queue,
            cron_expr=task.cron_exp,
            args=[task],
            job_id=f"fetch_{task.id}",
            tag="定时抓取",
        )
        print_info(f"已注册抓取任务: {task.name} ({task.cron_exp})")

    status = scheduler.get_scheduler_status()
    if not status['running']:
        scheduler.start()


def reload_fetch_jobs():
    """重载抓取任务（仅清掉本调度器内的 fetch 任务，再注册一次）"""
    print_info("【抓取任务】重载")
    scheduler.clear_all_jobs()
    start_fetch_jobs()


def run_fetch_task(task_id: str) -> Optional[List[FetchTask]]:
    """手动触发一次抓取任务（入队执行）"""
    tasks = get_active_fetch_tasks(task_id)
    if not tasks:
        print_warning(f"抓取任务[{task_id}]不存在或未启用")
        return None
    for task in tasks:
        add_fetch_to_queue(task)
    return tasks
