"""注册「文章存储周期清理」定时任务（使用 jobs.mps 中的同一 TaskScheduler）。"""
from core.config import cfg
from core.print import print_info, print_success
from core.task import TaskScheduler


def register_article_retention_job(scheduler: TaskScheduler) -> None:
    if not cfg.get("article.retention.enabled", False):
        return
    from core.article_retention import purge_expired_articles

    cron_expr = (cfg.get("article.retention.cron", "0 4 * * *") or "0 4 * * *").strip()

    def run_purge() -> None:
        purge_expired_articles()

    job_id = scheduler.add_cron_job(
        run_purge,
        cron_expr=cron_expr,
        job_id="werss_article_retention",
        tag="文章存储周期清理",
    )
    print_success(f"已注册文章存储周期清理任务: {job_id}, cron={cron_expr}")
    print_info(
        f"文章存储周期：保留 {cfg.get('article.retention.days', 7)} 天，"
        f"基准={cfg.get('article.retention.basis', 'created_at')}"
    )
    status = scheduler.get_scheduler_status()
    if not status.get("running"):
        scheduler.start()
