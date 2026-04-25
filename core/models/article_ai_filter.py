from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, Text

from .base import Base


class ArticleAiFilter(Base):
    """文章 AI 过滤结果，保留可恢复的判定记录。"""

    __tablename__ = "article_ai_filters"

    article_id = Column(String(255), primary_key=True)
    decision = Column(String(32), nullable=False, default="keep")
    category = Column(String(64), nullable=True)
    confidence = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    model_name = Column(String(255), nullable=True)
    source_title = Column(String(1000), nullable=True)
    source_tags = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

