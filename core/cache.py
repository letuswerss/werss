"""
简单的内存缓存工具模块
用于缓存文章列表等查询结果，减少数据库压力
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
import hashlib
import json
from threading import Lock
from core.config import cfg

# 缓存存储
_cache: dict[str, tuple[Any, datetime]] = {}
_cache_lock = Lock()

# 默认缓存过期时间（秒），可从配置文件读取
DEFAULT_TTL = cfg.get("cache.ttl", 300)  # 默认5分钟


def get_cache_key(*args, **kwargs) -> str:
    """
    生成缓存键
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        缓存键字符串
    """
    # 将参数序列化为字符串
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    # 使用 MD5 生成固定长度的键
    return hashlib.md5(key_str.encode('utf-8')).hexdigest()


def get_cache(cache_key: str, ttl: Optional[int] = None) -> Optional[Any]:
    """
    从缓存中获取数据
    
    Args:
        cache_key: 缓存键
        ttl: 缓存过期时间（秒），如果为 None 则使用默认值
        
    Returns:
        缓存的数据，如果不存在或已过期则返回 None
    """
    with _cache_lock:
        if cache_key not in _cache:
            return None
        
        data, expiry = _cache[cache_key]
        
        # 检查是否过期
        if datetime.now() >= expiry:
            del _cache[cache_key]
            return None
        
        return data


def set_cache(cache_key: str, data: Any, ttl: Optional[int] = None) -> None:
    """
    设置缓存
    
    Args:
        cache_key: 缓存键
        data: 要缓存的数据
        ttl: 缓存过期时间（秒），如果为 None 则使用默认值
    """
    if ttl is None:
        ttl = DEFAULT_TTL
    
    expiry = datetime.now() + timedelta(seconds=ttl)
    
    with _cache_lock:
        _cache[cache_key] = (data, expiry)


def clear_cache(cache_key: Optional[str] = None) -> None:
    """
    清除缓存
    
    Args:
        cache_key: 要清除的缓存键，如果为 None 则清除所有缓存
    """
    with _cache_lock:
        if cache_key is None:
            _cache.clear()
        elif cache_key in _cache:
            del _cache[cache_key]


def clear_cache_pattern(pattern: str) -> None:
    """
    清除匹配模式的缓存键
    
    Args:
        pattern: 缓存键前缀模式，例如 "articles:" 会清除所有以 "articles:" 开头的缓存
    """
    with _cache_lock:
        keys_to_delete = [key for key in _cache.keys() if key.startswith(pattern)]
        for key in keys_to_delete:
            del _cache[key]


def cache_decorator(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒），如果为 None 则使用默认值
        key_prefix: 缓存键前缀
        
    Usage:
        @cache_decorator(ttl=300, key_prefix="articles:")
        async def get_articles(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = get_cache_key(*args, **kwargs)
            if key_prefix:
                cache_key = f"{key_prefix}{cache_key}"
            
            # 尝试从缓存获取
            cached_data = get_cache(cache_key, ttl)
            if cached_data is not None:
                return cached_data
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            set_cache(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cleanup_expired_cache() -> int:
    """
    清理过期的缓存
    
    Returns:
        清理的缓存数量
    """
    now = datetime.now()
    cleaned = 0
    
    with _cache_lock:
        keys_to_delete = [
            key for key, (_, expiry) in _cache.items()
            if now >= expiry
        ]
        for key in keys_to_delete:
            del _cache[key]
            cleaned += 1
    
    return cleaned


def get_cache_stats() -> dict:
    """
    获取缓存统计信息
    
    Returns:
        包含缓存数量、内存使用等信息的字典
    """
    with _cache_lock:
        now = datetime.now()
        total = len(_cache)
        expired = sum(1 for _, expiry in _cache.values() if now >= expiry)
        active = total - expired
        
        return {
            "total": total,
            "active": active,
            "expired": expired
        }

