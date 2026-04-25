from .base import Base, Column, String, Integer, DateTime
from datetime import datetime


class TagClusterMember(Base):
    __tablename__ = "tag_cluster_members"

    id = Column(String(255), primary_key=True)
    cluster_id = Column(String(255), nullable=False, index=True)
    tag_id = Column(String(255), nullable=False, index=True)
    member_score = Column(Integer, default=0, nullable=False)
    cluster_version = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
