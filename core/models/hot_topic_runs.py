"""热点发现任务运行记录表"""
from .base import Base, Column, String, Integer, Text, DateTime
from datetime import datetime


class HotTopicRun(Base):
    """热点发现任务运行记录"""
    __tablename__ = 'hot_topic_runs'

    id = Column(String(255), primary_key=True)
    window_days = Column(Integer, default=3)
    article_count = Column(Integer, default=0)
    status = Column(String(50), default='pending')  # pending/running/success/failed
    model_name = Column(String(255))
    prompt_version = Column(String(100))
    raw_request = Column(Text)
    raw_response = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<HotTopicRun(id={self.id}, status={self.status}, window_days={self.window_days})>"
