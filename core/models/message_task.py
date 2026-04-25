# 从 sqlalchemy 导入所需的列类型和数据类型
from .base import Base,Column, Integer, String, DateTime,JSON,Text
# 从 datetime 模块导入 datetime 类，用于处理日期和时间
from datetime import datetime

# 定义 MessageTask 类，继承自 Base 基类
class MessageTask(Base):
    from_attributes = True
    # 指定数据库表名为 message_tasks
    __tablename__ = 'message_tasks'
    
    # 定义 id 字段，作为主键，同时创建索引
    id = Column(String(255), primary_key=True, index=True)
    # 定义消息类型字段，不允许为空
    message_type = Column(Integer, nullable=False)
    # 定义消息内容字段，使用 JSON 类型存储
    name = Column(String(100), nullable=False)

    # 定义消息模板字段，不允许为空
    message_template = Column(Text, nullable=False)
    # 定义发送接口
    web_hook_url = Column(String(500), nullable=False)
    # 定义需要通知的微信公众号ID集合
    mps_id = Column(Text, nullable=False)
    # 定义 cron_exp 表达式
    cron_exp=Column(String(100),nullable='* * 1 * *')
    # 定义任务状态字段，默认值为 pending
    status = Column(Integer, default=0)
    # 定义创建时间字段，默认值为当前 UTC 时间
    created_at = Column(DateTime)
    # 定义更新时间字段，默认值为当前 UTC 时间，更新时自动更新为当前时间
    updated_at = Column(DateTime )