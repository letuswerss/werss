from .base import Base, Column, String, Integer, DateTime
from datetime import datetime


class TagSimilarity(Base):
    __tablename__ = "tag_similarities"

    id = Column(String(255), primary_key=True)
    tag_id = Column(String(255), nullable=False, index=True)
    similar_tag_id = Column(String(255), nullable=False, index=True)
    score = Column(Integer, nullable=False, default=0)
    embedding_score = Column(Integer, nullable=False, default=0)
    cooccurrence_score = Column(Integer, nullable=False, default=0)
    lexical_score = Column(Integer, nullable=False, default=0)
    cluster_version = Column(String(64), nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)

