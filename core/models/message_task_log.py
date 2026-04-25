# 从 sqlalchemy 导入所需的列类型和数据类型
from .base import Base,Column, Integer, String, DateTime,JSON,Text
# 从 datetime 模块导入 datetime 类，用于处理日期和时间
from datetime import datetime

# 定义 MessageTaskLog 类，继承自 Base 基类
class MessageTask(Base):
    from_attributes = True
    # 指定数据库表名为 message_tasks
    __tablename__ = 'message_tasks_logs'
    
    # 定义 id 字段，作为主键，同时创建索引
    id = Column(String(255), primary_key=True, index=True)
    # 任务ID
    task_id = Column(String(255), nullable=False)
    # 公众号ID
    mps_id = Column(String(255), nullable=False)
    # 更新数量 
    update_count=Column(Integer,default=0)
    # 日志
    log=Column(Text,nullable=True)
    # 定义任务状态字段，默认值为 pending
    status = Column(Integer, default=0)
    # 定义创建时间字段，默认值为当前 UTC 时间
    created_at = Column(DateTime)
    # 定义更新时间字段，默认值为当前 UTC 时间，更新时自动更新为当前时间
    updated_at = Column(DateTime )