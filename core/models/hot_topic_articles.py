"""热点主题-文章关联表"""
from .base import Base, Column, String, DateTime
from datetime import datetime


class HotTopicArticle(Base):
    """热点主题与文章的关联"""
    __tablename__ = 'hot_topic_articles'

    id = Column(String(255), primary_key=True)
    topic_id = Column(String(255), nullable=False, index=True)
    article_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<HotTopicArticle(topic_id={self.topic_id}, article_id={self.article_id})>"
