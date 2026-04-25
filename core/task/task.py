import threading
import random
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Callable, Any, Optional
from core.log import logger
from core.print import print_info, print_error, print_warning
import uuid
# 设置日志

class TaskScheduler:
    """
    线程调度器类，支持cron定时任务调度
    使用APScheduler作为底层调度引擎

    Cron表达式说明:
    一个cron表达式有5个或6个空格分隔的时间字段，格式为:
        ┌───────────── 秒 (0 - 59) (6位格式)
        │ ┌───────────── 分钟 (0 - 59)
        │ │ ┌───────────── 小时 (0 - 23)
        │ │ │ ┌───────────── 日 (1 - 31)
        │ │ │ │ ┌───────────── 月 (1 - 12 或 JAN-DEC)
        │ │ │ │ │ ┌───────────── 星期 (0 - 6 或 SUN-SAT，0是周日)
        │ │ │ │ │ │
        * * * * * *
        或
        * * * * * (5位格式)

    特殊字符:
        *   任意值
        ,   值列表分隔符 (如 "MON,WED,FRI")
        -   范围 (如 "9-17" 表示9点到17点)
        /   步长 (如 "0/15" 表示从0开始每15分钟)
        ?   日或星期字段无特定值 (只能用在日或星期字段)

    常用示例:
        "0 0 * * *"     每天午夜执行 (5位)
        "0 9 * * MON"   每周一上午9点执行 (5位)
        "0 */6 * * *"   每6小时执行一次 (5位)
        "0 9-17 * * MON-FRI" 工作日每小时从9点到17点执行 (5位)
        "0 0 1 * *"     每月第一天午夜执行 (5位)
        "0 0 1 1 *"     每年1月1日午夜执行 (5位)
        "30 * * * * *"  每分钟的第30秒执行 (6位)
        "0 0 0 * * *"   每天午夜执行 (6位)
        "0 0 9 * * MON" 每周一上午9点执行 (6位)
    """
    
    def __init__(self):
        """初始化调度器和线程锁"""
        self._scheduler = BackgroundScheduler()
        self._lock = threading.Lock()
        self._jobs = {}

    def add_cron_job(self,
                     func: Callable,
                     cron_expr: str,
                     args: Optional[tuple] = None,
                     kwargs: Optional[dict] = None,
                     job_id: Optional[str] = None,
                     tag: str = ""
                     ) -> str:
        """
        添加一个cron定时任务
        
        :param func: 要执行的函数
        :param cron_expr: cron表达式，如"* * * * *"
        :param args: 函数的位置参数
        :param kwargs: 函数的关键字参数
        :param job_id: 任务ID，如果不指定则自动生成
        :return: 任务ID
        """
        with self._lock:
            try:
                logger.info(f"Adding cron job with expression: {cron_expr}")
                
                # 解析cron表达式为各个字段
                fields = cron_expr.split()
                if len(fields) == 5:
                    # 5位格式: 分 时 日 月 周
                    minute, hour, day, month, day_of_week = fields
                    second = "0"  # 默认秒为0
                elif len(fields) == 6:
                    # 6位格式: 秒 分 时 日 月 周
                    second, minute, hour, day, month, day_of_week = fields
                else:
                    error_msg = f"Invalid cron expression: {cron_expr}. Expected 5 or 6 fields."
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                # 处理随机时间范围
                def parse_random_field(field: str, field_name: str):
                    # 假设我们要解析的格式是 "*/1~3" 或 "1~3-3~10"
                    import re
                    try:
                        # 使用正则表达式匹配格式
                        pattern = r'(\d+)\~(\d+)'
                        match = re.findall(pattern, field)
                        if match:
                            # 提取匹配的组
                            start, end = match[0]
                            step = random.randint(int(start), int(end))
                            field = field.replace(f"{start}~{end}", str(step))
                    except:
                        pass
                    return field

                second = parse_random_field(second, 'second')
                minute = parse_random_field(minute, 'minute')
                hour = parse_random_field(hour, 'hour')
                day = parse_random_field(day, 'day')
                month = parse_random_field(month, 'month')
                day_of_week_original = parse_random_field(day_of_week, 'day_of_week')

                def translate_day_of_week(dow_str: str) -> str:
                    """将标准cron的星期(0=周日)转换为APScheduler的星期(0=周一)"""
                    import re
                    # 如果字段是 "*" 或 "?"，或者包含字母，则不处理
                    if not re.search(r'\d', dow_str) or re.search(r'[a-zA-Z]', dow_str):
                        return dow_str

                    def replacer(match):
                        num = int(match.group(0))
                        if num == 0:
                            return '6'
                        elif num == 7:  # 标准cron的周日别名 (兼容)
                            return '6'
                        else:
                            return str(num - 1)

                    return re.sub(r'\d+', replacer, dow_str)

                day_of_week = translate_day_of_week(day_of_week_original)

                # 生成job_id
                job_id = job_id or str(uuid.uuid4())

                trigger = CronTrigger(
                    second=second,
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                )
                
                # 包装任务函数以捕获异常
                def wrapped_func(*args, **kwargs):
                    try:
                        logger.info(f"【定时任务】开始执行任务 {tag} {job_id or 'anonymous'}")
                        result = func(*args, **kwargs)
                        logger.info(f"【定时任务】任务 {tag} {job_id or 'anonymous'} 执行完成")
                        return result
                    except Exception as e:
                        logger.error(f"【定时任务】任务 {tag} {job_id or 'anonymous'} 执行失败: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
                        raise
                
                job = self._scheduler.add_job(
                    wrapped_func,
                    trigger=trigger,
                    args=args,
                    kwargs=kwargs,
                    id=str(job_id)
                )
                self._jobs[job.id] = job
                
                # 安全地获取下次执行时间
                # 注意：在调度器未启动时，Job 对象可能没有 next_run_time 属性
                try:
                    if self._scheduler.running:
                        # 调度器已启动，可以直接访问 next_run_time
                        if hasattr(job, 'next_run_time') and job.next_run_time:
                            next_run = job.next_run_time.isoformat()
                        else:
                            next_run = "未计划"
                    else:
                        # 调度器未启动时，使用 trigger 计算下次执行时间
                        from datetime import datetime
                        next_run_time = trigger.get_next_fire_time(None, datetime.now())
                        next_run = next_run_time.isoformat() if next_run_time else "未计划（调度器未启动）"
                except Exception as e:
                    # 如果计算失败，使用默认值
                    next_run = f"计算失败: {str(e)}"
                
                logger.info(f"【定时任务】成功添加任务 {tag} {job.id}, cron表达式: {cron_expr}, 下次执行时间: {next_run}")
                print_info(f"【定时任务】成功添加任务 {tag} {job.id}, cron表达式: {cron_expr}, 下次执行时间: {next_run}")
                return job.id
            except Exception as e:
                logger.error(f"Failed to add cron job: {str(e)}")
                raise
    
    def remove_job(self, job_id: str) -> bool:
        """
        移除指定任务
        
        :param job_id: 要移除的任务ID
        :return: 是否成功移除
        """
        with self._lock:
            if job_id in self._jobs:
                self._scheduler.remove_job(job_id)
                del self._jobs[job_id]
                return True
            return False
    
    def clear_all_jobs(self) -> int:
        """
        清除所有任务，包括正在运行的任务
        
        :return: 被删除的任务数量
        """
        with self._lock:
            job_count = len(self._jobs)
            if job_count > 0:
                # 先终止所有正在运行的任务
                for job in self._scheduler.get_jobs():
                    try:
                        self._scheduler.remove_job(job.id)
                    except Exception as e:
                        logger.warning(f"Failed to remove job {job.id}: {str(e)}")
                
                # 清除所有计划任务
                self._scheduler.remove_all_jobs()
                self._jobs.clear()
                logger.info(f"Removed all {job_count} jobs")
            return job_count
    
    def start(self) -> None:
        """启动调度器"""
        with self._lock:
            if self._scheduler.running:
                logger.warning("Scheduler is already running")
                print_warning("调度器已经在运行中")
                return
                
            try:
                logger.info("Starting scheduler...")
                print_info("正在启动调度器...")
                self._scheduler.start()
                logger.info("Scheduler started successfully")
                print_info(f"调度器启动成功，当前任务数: {len(self._jobs)}")
                # 打印所有任务的下次执行时间
                for job_id, job in self._jobs.items():
                    next_run = self._get_job_next_run_time(job) or "未计划"
                    print_info(f"  任务 {job_id} 下次执行时间: {next_run}")
            except Exception as e:
                logger.error(f"Failed to start scheduler: {str(e)}")
                print_error(f"启动调度器失败: {str(e)}")
                raise
    
    def shutdown(self, wait: bool = True) -> None:
        """
        关闭调度器
        
        :param wait: 是否等待所有任务完成
        """
        with self._lock:
            if self._scheduler.running:
                self._scheduler.shutdown(wait=wait)
                self._jobs.clear()
    
    def get_job_ids(self) -> list[str]:
        """获取所有任务ID"""
        with self._lock:
            return list(self._jobs.keys())
    
    def __enter__(self):
        """支持上下文管理协议"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理协议"""
        self.shutdown()

    def _get_job_next_run_time(self, job) -> str:
        """安全地获取任务的下次执行时间"""
        try:
            if hasattr(job, 'next_run_time') and job.next_run_time:
                return job.next_run_time.isoformat()
            elif hasattr(job, 'trigger'):
                # 如果调度器未启动，尝试使用 trigger 计算
                from datetime import datetime
                next_run_time = job.trigger.get_next_fire_time(None, datetime.now())
                return next_run_time.isoformat() if next_run_time else None
            else:
                return None
        except Exception as e:
            logger.warning(f"获取任务 {job.id if hasattr(job, 'id') else 'unknown'} 的下次执行时间失败: {str(e)}")
            return None
    
    def get_scheduler_status(self) -> dict:
        """
        获取调度器状态信息
        
        :return: 包含调度器状态的字典
        """
        with self._lock:
            return {
                'running': self._scheduler.running,
                'job_count': len(self._jobs),
                'next_run_times': [
                    (job_id, self._get_job_next_run_time(job))
                    for job_id, job in self._jobs.items()
                ]
            }

    def get_job_details(self, job_id: str) -> dict:
        """
        获取任务详细信息
        
        :param job_id: 任务ID
        :return: 包含任务详情的字典
        """
        with self._lock:
            if job_id not in self._jobs:
                raise ValueError(f"Job {job_id} not found")
            
            job = self._jobs[job_id]
            return {
                'id': job.id,
                'name': job.name,
                'trigger': str(job.trigger),
                'next_run_time': self._get_job_next_run_time(job),
                'last_run_time': job.last_run_time.isoformat() if hasattr(job, 'last_run_time') and job.last_run_time else None,
                'last_run_result': job.last_run_result if hasattr(job, 'last_run_result') else None
            }

if __name__ == "__main__":
    # 示例用法
    def sample_task():
        print("定时任务执行中...")
    
    with TaskScheduler() as scheduler:
        # 添加每分钟执行一次的任务
        job_id = scheduler.add_cron_job(sample_task, "* * * * * *")
        print(f"已添加任务: {job_id}")
        input("按Enter键退出...\n")
    pass