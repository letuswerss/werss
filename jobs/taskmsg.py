from typing import Union
from core.db import Db
from core.config import cfg
from core.models import MessageTask
DB = Db()
DB.init(cfg.get("db"))
def get_message_task(job_id:Union[str, list]=None) -> list[MessageTask]:

    """
    获取消息任务详情
    
    参数:
        job_id: 单个消息任务ID或ID列表
        
    返回:
        包含消息任务详情的列表，或空列表如果任务不存在
    """
    try:
        session=DB.get_session()
        # 手动过期所有对象
        session.expire_all()
        query=session.query(MessageTask).filter(MessageTask.status==1)
        if job_id:
            if isinstance(job_id, list):
                query=query.filter(MessageTask.id.in_(job_id))
            else:
                query=query.filter(MessageTask.id==job_id)
        message_task = query.all()
        if not message_task:
            return None
        return message_task
    except Exception as e:
        print(e)
    return None