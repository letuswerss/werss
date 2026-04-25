"""
NotifyTask 模型：定时推送任务

将原 MessageTask 中的「渲染模板 + 推送 webhook」职责单独抽出来：
- 只负责按 cron 从数据库取一段时间的文章，渲染模板后推到 webhook
- 不负责任何文章采集
"""
from .base import Base, Column, Integer, String, DateTime, Text


class NotifyTask(Base):
    from_attributes = True
    __tablename__ = 'notify_tasks'

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    message_type = Column(Integer, nullable=False, default=0)
    message_template = Column(Text, nullable=False, default="")
    web_hook_url = Column(String(500), nullable=True)
    mps_id = Column(Text, nullable=False, default="[]")
    cron_exp = Column(String(100), nullable=False, default="0 9 * * *")
    status = Column(Integer, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
