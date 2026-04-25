from datetime import datetime

from .base import Base, Column, String, Integer, DateTime


class TagClusterAlias(Base):
    __tablename__ = "tag_cluster_aliases"

    id = Column(String(255), primary_key=True)
    alias_cluster_id = Column(String(255), nullable=False, index=True)
    cluster_id = Column(String(255), nullable=False, index=True)
    overlap_score = Column(Integer, default=0, nullable=False)
    cluster_version = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
