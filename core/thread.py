import threading
import time

class ThreadManager(threading.Thread):
    """多线程管理类，支持启动、停止和强制停止操作"""
    
    def __init__(self, target=None, name=None, args=(), kwargs=None):
        """
        初始化线程管理器
        :param target: 线程执行的函数
        :param name: 线程名称
        :param args: 函数参数
        :param kwargs: 函数关键字参数
        """
        super().__init__(target=target, name=name, args=args, kwargs=kwargs or {})
        self._stop_event = threading.Event()  # 优雅停止标志
        self._force_stop = False  # 强制停止标志
        self._lock = threading.Lock()  # 线程安全锁
        
    def start(self):
        """启动线程"""
        if not self.is_alive():
            super().start()
        return self
    
    def stop(self):
        """优雅停止线程，等待线程完成当前任务"""
        with self._lock:
            self._stop_event.set()
    
    def force_stop(self):
        """强制停止线程，不等待任务完成"""
        with self._lock:
            self._force_stop = True
            self._stop_event.set()
    
    def run(self):
        """线程运行逻辑"""
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except Exception as e:
            print(f"线程 {self.name} 发生异常: {e}")
        finally:
            print(f"线程 {self.name} 已停止")

# 示例用法
if __name__ == "__main__":
    def example_task():
        while True:
            print("线程运行中...")
            time.sleep(1)
    
    # 初始化并返回thread对象
    thread = ThreadManager(target=example_task, name="示例线程")
    
    # 启动线程
    thread.start()
    
    # 5秒后优雅停止
    time.sleep(5)
    thread.stop()
    
    # 或者强制停止
    # thread.force_stop()