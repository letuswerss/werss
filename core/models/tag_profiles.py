from .base import Base, Column, String, Integer, DateTime, JSON
from datetime import datetime


class TagProfile(Base):
    __tablename__ = "tag_profiles"

    tag_id = Column(String(255), primary_key=True)
    profile_text = Column(String(8000), nullable=False)
    profile_hash = Column(String(64), nullable=False, index=True)
    article_count = Column(Integer, default=0, nullable=False)
    sample_titles = Column(JSON, nullable=True)
    co_tags = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)

