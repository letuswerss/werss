"""API Key 相关数据模型"""
from .base import Base, Column, String, DateTime, Boolean, Text, ForeignKey, Integer
from datetime import datetime


class ApiKey(Base):
    """API Key 表"""
    __tablename__ = 'api_keys'
    
    id = Column(String(255), primary_key=True)
    key = Column(String(255), unique=True, nullable=False, index=True)  # API Key 值
    name = Column(String(255), nullable=False)  # API Key 名称/描述
    user_id = Column(String(255), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)  # 关联用户ID
    permissions = Column(Text)  # 权限列表（JSON格式字符串）
    is_active = Column(Boolean, default=True, nullable=False)  # 是否启用
    last_used_at = Column(DateTime, nullable=True)  # 最后使用时间
    created_at = Column(DateTime, default=datetime.now, nullable=False)  # 创建时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)  # 更新时间
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, name={self.name}, user_id={self.user_id}, is_active={self.is_active})>"


class ApiKeyLog(Base):
    """API Key 使用日志表"""
    __tablename__ = 'api_key_logs'
    
    id = Column(String(255), primary_key=True)
    api_key_id = Column(String(255), ForeignKey('api_keys.id', ondelete='CASCADE'), nullable=False, index=True)  # API Key ID
    endpoint = Column(String(500), nullable=False)  # 调用的接口路径
    method = Column(String(10), nullable=False)  # HTTP 方法
    ip_address = Column(String(50), nullable=True)  # 客户端IP
    user_agent = Column(String(500), nullable=True)  # 用户代理
    status_code = Column(Integer, nullable=False)  # 响应状态码
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)  # 调用时间
    
    def __repr__(self):
        return f"<ApiKeyLog(id={self.id}, api_key_id={self.api_key_id}, endpoint={self.endpoint}, method={self.method}, status_code={self.status_code})>"

