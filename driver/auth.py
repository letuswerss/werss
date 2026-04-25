import threading
from driver.base import WX_InterFace
import os
from core.task import TaskScheduler
from driver.success import Success

def auth():
    def run_auth():
        wx=WX_InterFace()
        # wx.Token(callback=Success)
        wx.switch_account()
    
    thread = threading.Thread(target=run_auth)
    thread.start()
    thread.join()  # 可选：等待完成
if os.getenv('WE_RSS.AUTH',False):
    auth_task=TaskScheduler()
    if os.getenv('DEBUG',False):
        auth_task.add_cron_job(auth, "*/1 * * * *",tag="授权定时更新")
    else:
        auth_task.add_cron_job(auth, "0 */1 * * *",tag="授权定时更新")
    auth_task.start()