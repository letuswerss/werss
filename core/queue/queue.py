import queue
import threading
import time
import gc
from typing import Callable, Any, Optional
from core.print import print_error, print_info, print_warning, print_success
class TaskQueueManager:
    """任务队列管理器，用于管理和执行排队任务"""
    
    def __init__(self,maxsize=0,tag:str=""):
        """初始化任务队列"""
        self._queue = queue.Queue(maxsize=maxsize)
        self._lock = threading.Lock()
        self._is_running = False
        self.tag=tag
        
    def add_task(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """添加任务到队列
        
        Args:
            task: 要执行的任务函数
            *args: 任务函数的参数
            **kwargs: 任务函数的关键字参数
        """
        with self._lock:
            self._queue.put((task, args, kwargs))
        print_success(f"{self.tag}队列任务添加成功\n")
    def run_task_background(self)->None:
        threading.Thread(target=self.run_tasks, daemon=True).start()  
        print_warning("队列任务后台运行")
    def run_tasks(self, timeout: float = 1.0) -> None:
        """执行队列中的所有任务，并持续运行以接收新任务
        
        Args:
            timeout: 等待新任务的超时时间(秒)
        """
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            
        try:
            while self._is_running:
                time.sleep(0.1)  # 避免过于频繁的任务获取 
                try:
                    # 阻塞获取任务，避免CPU空转
                    task, args, kwargs = self._queue.get(timeout=timeout)
                    
                    try:
                        # 记录任务开始时间
                        start_time = time.time()
                        print_info(f"\n【队列任务】开始执行任务: {task.__name__ if hasattr(task, '__name__') else str(task)}")
                        print_info(f"【队列任务】任务参数数量: {len(args)} 个位置参数, {len(kwargs)} 个关键字参数")
                        task(*args, **kwargs)
                        # 记录任务执行时间
                        duration = time.time() - start_time
                        print_info(f"\n【队列任务】任务执行完成，耗时: {duration:.2f}秒")
                    except Exception as e:
                        print_error(f"【队列任务】任务执行失败: {e}")
                        import traceback
                        traceback.print_exc()
                        # raise
                    finally:
                        # 确保任务完成标记和资源释放
                        self._queue.task_done()
                        # 强制垃圾回收
                        gc.collect()
                    
                except queue.Empty:
                    # 超时无任务，继续检查运行状态
                    continue
                    
        finally:
            # 确保停止状态设置和资源清理
            with self._lock:
                self._is_running = False
            # 清理可能残留的资源
            gc.collect()
    
    def stop(self) -> None:
        """停止任务执行"""
        with self._lock:
            self._is_running = False
    
    def get_queue_info(self) -> dict:
        """
        获取队列的当前状态信息
        
        返回:
            dict: 包含队列信息的字典，包括:
                - is_running: 队列是否正在运行
                - pending_tasks: 等待执行的任务数量
        """
        with self._lock:
            return {
                'is_running': self._is_running,
                'pending_tasks': self._queue.qsize()
            }
            
    def clear_queue(self) -> None:
        """清空队列中的所有任务"""
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except queue.Empty:
                    break
            print_success("队列已清空")
            
    def delete_queue(self) -> None:
        """删除队列(停止并清空所有任务)"""
        with self._lock:
            self._is_running = False
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except queue.Empty:
                    break
            print_success("队列已删除")
TaskQueue = TaskQueueManager(tag="默认队列")
TaskQueue.run_task_background()
if __name__ == "__main__":
    def task1():
        print("执行任务1")

    def task2(name):
        print(f"执行任务2，参数: {name}")

    manager = TaskQueueManager()
    manager.add_task(task1)
    manager.add_task(task2, "测试任务")
    manager.run_tasks()  # 按顺序执行任务1和任务2