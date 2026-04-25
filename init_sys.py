from core.models.user import User
from core.models.article import Article
# 导入所有模型以确保它们被注册到 Base.metadata
from core.models import ApiKey, ApiKeyLog
from core.db import Db,DB
from core.config import cfg
from core.auth import pwd_context
import time
import os
from core.print import print_info, print_error
def init_user(_db: Db):
    try:
      # 优先使用 WERSS_USERNAME/WERSS_PASSWORD，兼容 USERNAME/PASSWORD
      username = os.getenv("WERSS_USERNAME") or os.getenv("USERNAME", "admin")
      password = os.getenv("WERSS_PASSWORD") or os.getenv("PASSWORD", "admin@123")
      session=_db.get_session()
      # 检查用户是否已存在
      existing_user = session.query(User).filter(User.username == username).first()
      if existing_user:
          # 如果用户已存在，更新密码
          existing_user.password_hash = pwd_context.hash(password)
          session.commit()
          print_info(f"用户已存在，已更新密码。请使用以下凭据登录：{username}")
      else:
          # 如果用户不存在，创建新用户
          session.add(User(
              id=0,

              
              username=username,
              password_hash=pwd_context.hash(password),
              ))
          session.commit()
          print_info(f"初始化用户成功,请使用以下凭据登录：{username}")
    except Exception as e:
        print_error(f"Init user error: {str(e)}")
        pass
def sync_models():
     # 同步模型到表结构
         DB.create_tables()
         time.sleep(1)
         DB.migrate_tables()
         print_info("模型同步完成")

     

 
def init():
    sync_models()
    init_user(DB)

if __name__ == '__main__':
    init()