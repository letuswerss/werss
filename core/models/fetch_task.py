"""
FetchTask 模型：定时抓取任务

将原 MessageTask 中的「抓取」职责单独抽出来：
- 只负责按 cron 定时采集指定公众号的文章入库
- 不负责任何消息推送
"""
from .base import Base, Column, Integer, String, DateTime, Text


class FetchTask(Base):
    from_attributes = True
    __tablename__ = 'fetch_tasks'

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    mps_id = Column(Text, nullable=False, default="[]")
    cron_exp = Column(String(100), nullable=False, default="0 * * * *")
    max_page = Column(Integer, nullable=True)
    status = Column(Integer, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
