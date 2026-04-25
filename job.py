from jobs import start_job
if __name__ == '__main__':
    import init_sys as init
    init.init()
    # 启动定时任务
    start_job()
    input("按Enter键退出...\n")
    # def sample_task():
    #     print("定时任务执行中...")
    # from core.task import TaskScheduler
    # with TaskScheduler() as scheduler:
    #     # 添加每分钟执行一次的任务
    #     job_id = scheduler.add_cron_job(sample_task, "* * * * * *")
    #     print(f"已添加任务: {job_id}")
    #     input("按Enter键退出...\n")
    # pass