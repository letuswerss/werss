from fastapi import APIRouter, Request, HTTPException
import httpx
from fastapi.responses import Response
import os
import hashlib
import time
import json
from core.config import cfg
CACHE_DIR = cfg.get("cache.dir","data/cache")
CACHE_TTL = 3600  # 缓存过期时间1小时

os.makedirs(CACHE_DIR, exist_ok=True)

router = APIRouter(prefix="/res", tags=["资源反向代理"])

# 允许代理的微信图片/头像 CDN 域名。
# 注意：wx.qlogo.cn 是公众号头像常见来源，显式放行可避免前端图片外链访问不稳定。
_WX_ALLOWED_HOSTS = (
    "mmbiz.qpic.cn",
    "mmbiz.qlogo.cn",
    "mmecoa.qpic.cn",
    "wx.qlogo.cn",
    "thirdwx.qlogo.cn",
)


@router.api_route(
    "/logo/{path:path}",
    methods=["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"],
    operation_id="reverse_proxy_logo",
)
async def reverse_proxy(request: Request, path: str):
    """微信公众号图片代理：下载并缓存，统一前端图片加载入口。"""
    from urllib.parse import urlparse, urlunparse

    parsed_url = urlparse(path)

    # 兼容 starlette 把 :// 折成 :/ 的情况（FastAPI path 参数会丢一个斜杠）
    if not parsed_url.netloc and parsed_url.scheme and parsed_url.path.startswith("/"):
        rebuilt = f"{parsed_url.scheme}://{parsed_url.path.lstrip('/')}"
        if parsed_url.query:
            rebuilt += f"?{parsed_url.query}"
        parsed_url = urlparse(rebuilt)

    host = (parsed_url.hostname or "").lower()
    # 不在白名单的域名直接 301 回源（保持原协议，避免 https→http 触发 mixed content）
    if host not in _WX_ALLOWED_HOSTS:
        target = urlunparse(parsed_url) if parsed_url.scheme else path
        return Response(
            content="只允许反代微信图片 CDN。",
            status_code=301,
            headers={"Location": target},
        )

    # 微信 CDN 同时支持 https，统一升级为 https，避免在 https 站点上触发 mixed-content
    if parsed_url.scheme != "https":
        parsed_url = parsed_url._replace(scheme="https")
    path = urlunparse(parsed_url)
    
    # 生成缓存文件名（HEAD 和 GET 使用相同的缓存）
    cache_key = f"GET_{path}".encode('utf-8')  # HEAD 和 GET 共享缓存
    cache_filename = os.path.join(CACHE_DIR, hashlib.sha256(cache_key).hexdigest())
    
    # 检查缓存是否存在且有效
    if os.path.exists(cache_filename):
        file_mtime = os.path.getmtime(cache_filename)
        if time.time() - file_mtime < CACHE_TTL:
            # 读取缓存的状态码和响应头
            headers_filename = cache_filename + ".headers"
            if os.path.exists(headers_filename):
                with open(headers_filename, 'r', encoding='utf-8') as f:
                    headers = json.load(f)
            else:
                headers = {}
            
            media_type = headers.get("Content-Type", "image/jpeg")
            status_code = 200  # 默认状态码
            
            # HEAD 请求只返回响应头，不返回内容
            if request.method == "HEAD":
                return Response(
                    status_code=status_code,
                    headers=headers,
                    media_type=media_type
                )
            
            # GET 请求返回完整内容
            with open(cache_filename, 'rb') as f:
                content = f.read()
            
            return Response(
                content=content,
                status_code=status_code,
                headers=headers,
                media_type=media_type
            )
    
    # 缓存不存在或已过期，需要重新下载
    target_url = path
    
    # 设置常见浏览器图片请求头，提升外部图片加载兼容性。
    request_headers = {
        'User-Agent': cfg.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"),
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://mp.weixin.qq.com/',
        'Connection': 'keep-alive',
    }
    
    try:
        client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        request_data = await request.body()
        
        resp = await client.request(
            method=request.method if request.method != "HEAD" else "GET",  # HEAD 请求转换为 GET 来获取内容
            url=target_url,
            headers=request_headers,
            content=request_data if request_data else None
        )
        
        content = resp.content
        status_code = resp.status_code
        response_headers = dict(resp.headers)
        media_type = resp.headers.get("Content-Type", "image/jpeg")
        
        # 只缓存成功的响应
        if status_code == 200 and content:
            try:
                # 缓存响应内容
                with open(cache_filename, 'wb') as f:
                    f.write(content)
                
                # 缓存响应头
                headers_filename = cache_filename + ".headers"
                with open(headers_filename, 'w', encoding='utf-8') as f:
                    json.dump(response_headers, f, ensure_ascii=False)
            except Exception as e:
                from core.log import logger
                logger.warning(f"缓存响应失败: {str(e)}")
        
        # HEAD 请求只返回响应头
        if request.method == "HEAD":
            return Response(
                status_code=status_code,
                headers=response_headers,
                media_type=media_type
            )
        
        return Response(
            content=content,
            status_code=status_code,
            headers=response_headers,
            media_type=media_type
        )
    except httpx.TimeoutException:
        from core.log import logger
        logger.error(f"下载图片超时: {target_url}")
        return Response(
            content="下载图片超时",
            status_code=504,
            media_type="text/plain"
        )
    except Exception as e:
        from core.log import logger
        logger.error(f"下载图片失败: {target_url}, 错误: {str(e)}")
        return Response(
            content=f"下载图片失败: {str(e)}",
            status_code=500,
            media_type="text/plain"
        )