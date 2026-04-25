from datetime import datetime, timedelta
import jwt
import bcrypt
from functools import wraps
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from core.models import User as DBUser
from core.config import  cfg,API_BASE
from sqlalchemy.orm import Session
from core.models import User, ApiKey
import core.db  as db
from passlib.context import CryptContext
import json

DB=db.Db(tag="用户连接")
SECRET_KEY = cfg.get("secret","csol2025")  # 生产环境应使用更安全的密钥
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(cfg.get("token_expire_minutes",30))

class PasswordHasher:
    """自定义密码哈希器，替代passlib的CryptContext"""
    
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """验证密码是否匹配哈希"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def hash(password: str) -> str:
        """生成密码哈希"""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

# 密码哈希上下文
pwd_context = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_BASE}/auth/token",auto_error=False)

# 用户缓存字典
_user_cache = {}
# 登录失败次数记录
_login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5

def get_login_attempts(username: str) -> int:
    """获取用户登录失败次数"""
    return _login_attempts.get(username, 0)

def get_user(username: str) -> Optional[dict]:
    """从数据库获取用户，带缓存功能"""
    # 先检查缓存
    if username in _user_cache:
        return _user_cache[username]
        
    session = DB.get_session()
    try:
        user = session.query(DBUser).filter(DBUser.username == username).first()
        if user:
            # 转换为字典并存入缓存
            user_dict = user.__dict__.copy()
            # 移除 SQLAlchemy 内部属性（如 _sa_instance_state）
            user_dict.pop('_sa_instance_state', None)
            user_dict=User(**user_dict)
            _user_cache[username] = user_dict
            return user_dict
        return None
    except Exception as e:
        from core.print import print_error
        print_error(f"获取用户错误: {str(e)}")
        return None
        
def clear_user_cache(username: str):
    """清除指定用户的缓存"""
    if username in _user_cache:
        del _user_cache[username]

from apis.base import error_response
def authenticate_user(username: str, password: str) -> Optional[DBUser]:
    """验证用户凭据"""
    # 检查是否超过最大尝试次数
    if _login_attempts.get(username, 0) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=error_response(
                code=40101,
                message="用户名或密码错误，您的帐号已锁定，请稍后再试"
            )
        )
    
    user = get_user(username)

    if not user or not pwd_context.verify(password, user.password_hash):
        # 增加失败次数
        _login_attempts[username] = _login_attempts.get(username, 0) + 1
        remaining_attempts = MAX_LOGIN_ATTEMPTS - _login_attempts[username]
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=error_response(
                code=40101,
                message=f"用户名或密码错误，您还有{remaining_attempts}次机会"
            )
        )
    
    # 登录成功，清除失败记录
    if username in _login_attempts:
        del _login_attempts[username]
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def extract_api_key_from_request(request: Request) -> Optional[str]:
    """从请求头中提取 API Key
    
    支持两种方式：
    1. X-API-Key 头
    2. Authorization: Bearer <api_key>
    """
    # 方式1: 从 X-API-Key 头获取
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key
    
    # 方式2: 从 Authorization 头获取 (Bearer <api_key>)
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        api_key = authorization[7:]  # 去掉 "Bearer " 前缀
        # 如果看起来不像 JWT token（JWT 通常包含多个点），可能是 API Key
        if api_key and "." not in api_key:
            return api_key
        # 如果包含点，可能是 JWT，先尝试作为 JWT 处理，如果失败再作为 API Key
        # 这里先返回 None，让 JWT 验证先处理
    
    return None

async def get_current_user_by_api_key(api_key: str) -> Optional[dict]:
    """通过 API Key 获取当前用户"""
    if not api_key:
        return None
    
    session = DB.get_session()
    try:
        # 查询 API Key
        api_key_obj = session.query(ApiKey).filter(
            ApiKey.key == api_key,
            ApiKey.is_active == True
        ).first()
        
        if not api_key_obj:
            return None
        
        # 更新最后使用时间
        from datetime import datetime
        api_key_obj.last_used_at = datetime.now()
        session.commit()
        
        # 获取关联的用户
        user = session.query(DBUser).filter(DBUser.id == api_key_obj.user_id).first()
        if not user:
            return None
        
        # 解析权限（优先使用 API Key 的权限，如果没有则使用用户的权限）
        permissions = api_key_obj.permissions
        if not permissions:
            permissions = user.permissions
        
        # 转换为字典格式
        user_dict = user.__dict__.copy()
        user_dict.pop('_sa_instance_state', None)
        user_dict = User(**user_dict)
        
        return {
            "username": user.username,
            "role": user.role,
            "permissions": permissions,
            "original_user": user,
            "api_key_id": api_key_obj.id  # 添加 API Key ID，用于日志记录
        }
    except Exception as e:
        from core.print import print_error
        print_error(f"API Key 认证错误: {str(e)}")
        return None
    finally:
        session.close()

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme)
):
    """获取当前用户
    
    认证优先级：
    1. JWT Token（如果存在）
    2. API Key（如果 JWT Token 不存在）
    3. 返回 401（如果都没有）
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 优先尝试 JWT Token 认证
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            
            # 尝试从数据库获取用户，如果不存在则使用默认值（仅验证 token 有效性）
            user = get_user(username)
            if user is None:
                # Token 有效但数据库中没有用户，返回默认用户信息（允许 API 访问）
                return {
                    "username": username,
                    "role": "user",
                    "permissions": None,
                    "original_user": None
                }
                
            return {
                "username": user.username,
                "role": user.role,
                "permissions": user.permissions,
                "original_user": user
            }
        except jwt.PyJWTError:
            # JWT 验证失败，继续尝试 API Key
            pass
    
    # JWT Token 不存在或验证失败，尝试 API Key 认证
    api_key = extract_api_key_from_request(request)
    if api_key:
        user = await get_current_user_by_api_key(api_key)
        if user:
            return user
    
    # 两种认证方式都失败，返回 401
    raise credentials_exception

def requires_role(role: str):
    """检查用户角色的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or current_user.get('role') != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def requires_permission(permission: str):
    """检查用户权限的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or permission not in current_user.get('permissions', []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator