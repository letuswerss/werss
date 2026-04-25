"""注册「热点发现」定时任务"""
from core.config import cfg
from core.print import print_info, print_success, print_warning
from core.task import TaskScheduler


def register_hot_topics_job(scheduler: TaskScheduler) -> None:
    """
    注册热点发现定时任务

    Args:
        scheduler: TaskScheduler 实例
    """
    # 检查是否启用
    enabled = cfg.get("hot_topics.enabled", True)
    if not enabled:
        print_info("热点发现任务已禁用 (hot_topics.enabled = False)")
        return

    # 检查 LLM 配置
    import os
    api_key = cfg.get("openai.api_key", None) or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print_warning("OpenAI API Key 未配置，热点发现任务无法注册")
        return

    # 获取 cron 配置，默认每天早上 9 点执行
    cron_expr = (cfg.get("hot_topics.cron", "0 9 * * *") or "0 9 * * *").strip()

    def run_discovery():
        """执行热点发现"""
        from core.database import get_db
        from core.hot_topics.service import run_discovery_sync

        db = get_db()
        try:
            window_days = int(cfg.get("hot_topics.window_days", 3) or 3)
            max_topics = int(cfg.get("hot_topics.max_topics", 5) or 5)
            window_days = max(1, min(window_days, 30))
            max_topics = max(3, min(max_topics, 20))
            print_info("开始执行定时热点发现任务...")
            run_id, topic_count = run_discovery_sync(
                db, window_days=window_days, max_topics=max_topics
            )
            print_success(f"热点发现任务完成: run_id={run_id}, topic_count={topic_count}")
        except Exception as e:
            print_warning(f"热点发现任务失败: {str(e)}")
        finally:
            db.close()

    job_id = scheduler.add_cron_job(
        run_discovery,
        cron_expr=cron_expr,
        job_id="hot_topics_discovery",
        tag="热点发现",
    )

    print_success(f"已注册热点发现任务: {job_id}, cron={cron_expr}")

    window_days = cfg.get("hot_topics.window_days", 3)
    print_info(f"热点发现配置: 时间窗口={window_days} 天")

    # 如果调度器未运行，则启动
    status = scheduler.get_scheduler_status()
    if not status.get("running"):
        scheduler.start()
