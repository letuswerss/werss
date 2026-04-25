from .base import Base, Column, String, Integer, DateTime, Text
from datetime import datetime


class TagCluster(Base):
    __tablename__ = "tag_clusters"

    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    centroid_tag_id = Column(String(255), nullable=True, index=True)
    size = Column(Integer, default=0, nullable=False)
    cluster_version = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)

