from .base import Base, Column, String, Integer, DateTime, JSON
from datetime import datetime


class TagEmbedding(Base):
    __tablename__ = "tag_embeddings"

    id = Column(String(255), primary_key=True)
    tag_id = Column(String(255), nullable=False, index=True)
    embedding_provider = Column(String(64), nullable=False, index=True)
    embedding_model = Column(String(255), nullable=False)
    embedding_dimensions = Column(Integer, nullable=True)
    profile_hash = Column(String(64), nullable=False, index=True)
    vector = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)

