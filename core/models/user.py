from .base import Base, Column, String, Integer, DateTime, Boolean,Text
class User(Base):
    __tablename__ = 'users'
    id = Column(String(255), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(20))  # admin/editor/user
    permissions = Column(Text)  # 权限列表
    nickname = Column(String(50), default='')  # 昵称
    avatar = Column(String(255), default='/static/default-avatar.png')  # 头像
    email = Column(String(50), default='')
    
    # 原有字段保持不变
    mp_name = Column(String(255))
    mp_cover = Column(String(255))
    mp_intro = Column(String(255))
    status = Column(Integer)
    sync_time = Column(DateTime)
    update_time = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    faker_id = Column(String(255))

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        from core.auth import pwd_context
        return pwd_context.verify(password, self.password_hash)