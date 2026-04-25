from core.models.article import Article,DATA_STATUS
import core.db as db
from core.wx.base import WxGather
from time import sleep
from core.print import print_success,print_error
import random
from driver.wxarticle import Web
DB=db.Db(tag="内容修正")
def fetch_articles_without_content():
    """
    查询content为空的文章，调用微信内容提取方法获取内容并更新数据库
    """
    session = DB.get_session()
    ga=WxGather().Model()
    try:
        # 查询content为空的文章
        from sqlalchemy import or_
        articles = session.query(Article).filter(or_(Article.content.is_(None), Article.content == "")).limit(10).all()
        
        if not articles:
            print_warning("暂无需要获取内容的文章")
            return
        
        for article in articles:
            # 构建URL
            if article.url:
                url = article.url
            else:
                url = f"https://mp.weixin.qq.com/s/{article.id}"
            
            print(f"正在处理文章: {article.title}, URL: {url}")
            
            # 获取内容
            if cfg.get("gather.content_mode","web"):
                content=Web.get_article_content(url).get("content")
            else:
                content = ga.content_extract(url)
            sleep(random.randint(3,10))
            if content:
                # 更新内容
                article.content = content
                if  content=="DELETED":
                    print_error(f"获取文章 {article.title} 内容已被发布者删除")
                    article.status = DATA_STATUS.DELETED
                session.commit()
                print_success(f"成功更新文章 {article.title} 的内容")
            else:
                print_error(f"获取文章 {article.title} 内容失败")
                
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
    finally:
        Web.Close()
from core.task import TaskScheduler
from core.queue import TaskQueueManager
scheduler=TaskScheduler()
task_queue=TaskQueueManager()
task_queue.run_task_background()
from core.config import cfg
from core.print import print_success,print_warning
def start_sync_content():
    if not cfg.get("gather.content_auto_check",False):
        print_warning("自动检查并同步文章内容功能未启用")
        return
    interval=int(cfg.get("gather.content_auto_interval",1)) # 每隔多少分钟
    cron_exp=f"*/{interval} * * * *"
    task_queue.clear_queue()
    scheduler.clear_all_jobs()
    def do_sync():
        task_queue.add_task(fetch_articles_without_content)
    job_id=scheduler.add_cron_job(do_sync,cron_expr=cron_exp)
    print_success(f"已添自动同步文章内容任务: {job_id}")
    scheduler.start()
if __name__ == "__main__":
    fetch_articles_without_content()