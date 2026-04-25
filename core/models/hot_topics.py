"""热点主题表"""
from .base import Base, Column, String, Integer, Text, DateTime, JSON
from datetime import datetime


class HotTopic(Base):
    """热点主题"""
    __tablename__ = 'hot_topics'

    id = Column(String(255), primary_key=True)
    run_id = Column(String(255), nullable=False, index=True)
    topic_name = Column(String(500))
    summary = Column(Text)
    signals_json = Column(JSON)  # 存储字符串数组
    article_count = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<HotTopic(id={self.id}, topic_name={self.topic_name}, article_count={self.article_count})>"
