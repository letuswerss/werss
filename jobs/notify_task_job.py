"""
推送任务（NotifyTask）调度

只做一件事：按 cron 从 DB 取已有文章，渲染模板后推到 webhook。
不做任何文章采集。
"""
import json
from datetime import datetime
from typing import List, Union, Optional

import core.db as db
from core.log import logger
from core.models import NotifyTask
from core.models.feed import Feed
from core.notice import notice
from core.print import print_error, print_info, print_success, print_warning
from core.queue import TaskQueue
from core.task import TaskScheduler

_db = db.Db(tag="推送任务")
scheduler = TaskScheduler()


def get_active_notify_tasks(task_id: Union[str, list, None] = None) -> Optional[List[NotifyTask]]:
    """获取启用中的推送任务"""
    try:
        session = db.DB.get_session()
        session.expire_all()
        query = session.query(NotifyTask).filter(NotifyTask.status == 1)
        if task_id:
            if isinstance(task_id, list):
                query = query.filter(NotifyTask.id.in_(task_id))
            else:
                query = query.filter(NotifyTask.id == task_id)
        tasks = query.all()
        return tasks if tasks else None
    except Exception as e:
        logger.error(f"获取推送任务失败: {e}")
        return None


def get_feeds_for_task(task: NotifyTask) -> List[Feed]:
    """根据推送任务返回数据来源公众号；mps_id 为空时返回全部"""
    try:
        mps = json.loads(task.mps_id) if task.mps_id else []
    except Exception:
        mps = []

    if not mps:
        return _db.get_all_mps()
    ids = ",".join([item["id"] for item in mps if isinstance(item, dict) and "id" in item])
    feeds = _db.get_mps_list(ids) if ids else []
    return feeds if feeds else _db.get_all_mps()


def _collect_feed_articles(feed: Feed) -> dict:
    """从 DB 取该公众号当天文章 + 标签"""
    from .mps import get_today_articles, get_article_tags
    session = db.DB.get_session()
    try:
        articles = get_today_articles(feed.id)
        if not articles:
            return {"feed": feed, "articles": []}

        tags_by_article = get_article_tags(session, [a.id for a in articles])
        articles_list = []
        for article in articles:
            article_dict = {
                'id': article.id,
                'mp_id': article.mp_id,
                'title': article.title or '',
                'pic_url': article.pic_url or '',
                'url': article.url or '',
                'description': article.description or '',
                'publish_time': article.publish_time,
                'content': getattr(article, 'content', None),
                'tags': tags_by_article.get(article.id, []),
                'tag_names': tags_by_article.get(article.id, []),
            }
            pt = article_dict.get('publish_time')
            if pt:
                try:
                    if isinstance(pt, (int, float)):
                        article_dict['publish_time'] = datetime.fromtimestamp(pt).strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(pt, str) and pt.isdigit():
                        article_dict['publish_time'] = datetime.fromtimestamp(int(pt)).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
            articles_list.append(article_dict)
        return {"feed": feed, "articles": articles_list}
    finally:
        session.close()


def do_notify_task(task: NotifyTask):
    """执行一条推送任务"""
    if not task.web_hook_url:
        print_error(f"推送任务[{task.name}]未设置 webhook 地址，跳过")
        return

    feeds = get_feeds_for_task(task)
    if not feeds:
        print_warning(f"推送任务[{task.name}]没有可推送的公众号")
        return

    bundles = []
    for feed in feeds:
        try:
            bundle = _collect_feed_articles(feed)
            if bundle["articles"]:
                bundles.append(bundle)
        except Exception as e:
            print_error(f"准备 {feed.mp_name} 数据失败: {e}")

    if not bundles:
        print_warning(f"推送任务[{task.name}]当天没有可推送的文章")
        return

    total_articles = sum(len(b['articles']) for b in bundles)
    today_date = datetime.now().strftime("%Y-%m-%d")

    from core.lax import TemplateParser
    default_template = """{{ today }} 每日科技聚合资讯

{% for item in feeds_with_articles %}
## {{ item.feed.mp_name }}

{% for article in item.articles %}
- [**{{ article.title }}**]({{ article.url }}){% if article.tag_names %} 🏷️ {{= ', '.join(article.tag_names) if isinstance(article.tag_names, list) else str(article.tag_names) }}{% endif %}
{% endfor %}

{% endfor %}

---
📊 共 {{ total_articles }} 篇文章，来自 {{ feeds_count }} 个公众号
"""

    user_template = task.message_template or ""
    template = user_template if 'feeds_with_articles' in user_template else default_template

    parser = TemplateParser(template)
    data = {
        "feeds_with_articles": bundles,
        "total_articles": total_articles,
        "feeds_count": len(bundles),
        "task": task,
        'now': today_date,
        'today': today_date,
    }

    try:
        message = parser.render(data)
    except Exception as e:
        print_error(f"推送任务[{task.name}]模板渲染失败: {e}")
        return

    try:
        result = notice(task.web_hook_url, task.name, message)
        if result:
            print_success(f"【推送任务】{task.name} 推送成功，{len(bundles)} 个公众号 / {total_articles} 篇")
        else:
            print_error(f"【推送任务】{task.name} 推送失败")
    except Exception as e:
        print_error(f"推送任务[{task.name}]发送时出错: {e}")
        import traceback
        traceback.print_exc()


def add_notify_to_queue(task: NotifyTask):
    """把推送任务入队"""
    TaskQueue.add_task(do_notify_task, task)
    print_info(f"【推送任务】{task.name} 已入队列")


def start_notify_jobs(task_id: Union[str, list, None] = None):
    """注册所有启用的推送任务到调度器"""
    tasks = get_active_notify_tasks(task_id)
    if not tasks:
        print_info("没有启用的推送任务")
        return

    for task in tasks:
        if not task.cron_exp:
            print_error(f"推送任务[{task.id}]没有设置 cron 表达式")
            continue
        scheduler.add_cron_job(
            add_notify_to_queue,
            cron_expr=task.cron_exp,
            args=[task],
            job_id=f"notify_{task.id}",
            tag="定时推送",
        )
        print_info(f"已注册推送任务: {task.name} ({task.cron_exp})")

    status = scheduler.get_scheduler_status()
    if not status['running']:
        scheduler.start()


def reload_notify_jobs():
    """重载推送任务"""
    print_info("【推送任务】重载")
    scheduler.clear_all_jobs()
    start_notify_jobs()


def run_notify_task(task_id: str) -> Optional[List[NotifyTask]]:
    """手动触发一次推送任务（入队执行）"""
    tasks = get_active_notify_tasks(task_id)
    if not tasks:
        print_warning(f"推送任务[{task_id}]不存在或未启用")
        return None
    for task in tasks:
        add_notify_to_queue(task)
    return tasks
