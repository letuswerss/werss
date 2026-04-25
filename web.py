from fastapi import FastAPI, Request, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.models import OAuthFlowPassword
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from apis.auth import router as auth_router
from apis.user import router as user_router
from apis.article import router as article_router
from apis.mps import router as wx_router
from apis.res import router as res_router
from apis.rss import router as rss_router,feed_router
from apis.config_management import router as config_router
from apis.message_task import router as task_router
from apis.fetch_task import router as fetch_task_router
from apis.notify_task import router as notify_task_router
from apis.system_task import router as system_task_router
from apis.sys_info import router as sys_info_router
from apis.tags import router as tags_router
from apis.article_tag import router as article_tag_router
from apis.export import router as export_router
from apis.tools import router as tools_router
from apis.github_update import router as github_router
from apis.dashboard import router as dashboard_router
from apis.api_key import router as api_key_router
from apis.tag_clusters import router as tag_cluster_router
from apis.mcp import router as mcp_router
from apis.hot_topics import router as hot_topics_router
import apis
import os
from core.config import cfg,VERSION,API_BASE
import threading
from core.print import print_info, print_warning

# OpenAPI / Swagger 顶层说明（支持 Markdown）
_WERSS_OPENAPI_DESCRIPTION = f"""
WeRSS：微信公众号聚合、采集与阅读。

### 认证方式

1. **JWT（OAuth2 密码模式）**  
   - 调用 `{API_BASE}/auth/token`（`application/x-www-form-urlencoded`：`username`、`password`）获取 `access_token`  
   - 请求头：`Authorization: Bearer <jwt>`

2. **API Key**  
   - 在 Web 端 **API Key 管理** 创建密钥（格式 `werss_...`）  
   - 请求头：`X-API-Key: werss_你的密钥`  
   - 或：`Authorization: Bearer werss_你的密钥`（不含 `.` 时按 API Key 解析）

### 文章列表查询

`GET` / `POST` **`{API_BASE}/articles`** 支持：

| 参数 | 说明 |
|------|------|
| `offset`, `limit` | 分页 |
| `search` | 标题关键词（多词 OR） |
| `mp_id` | 公众号 |
| `publish_from` / `publish_to` | 发布时间戳（&lt;10¹² 视为秒，否则毫秒） |
| `publish_date_from` / `publish_date_to` | `YYYY-MM-DD`（UTC 日历日） |
| `tag_id` / `tag_ids` | 标签 ID，`tag_ids` 逗号分隔 |
| `tag_match` | `any`（默认，任一标签）或 `all`（同时包含全部） |

更完整的字段说明见仓库 **`docs/ARTICLE_QUERY_API.md`**。
"""

# 全局变量：标记定时任务是否已启动
_task_thread_started = False
_task_thread = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动和关闭事件"""
    # 启动时执行
    global _task_thread_started, _task_thread
    
    # 检查定时任务配置
    job_arg = cfg.args.job == "True" if hasattr(cfg, 'args') else False
    enable_job_config = cfg.get("server.enable_job", True)
    
    print_info(f"【应用启动】定时任务配置检查: -job参数={job_arg}, server.enable_job={enable_job_config}")
    
    if job_arg and enable_job_config:
        # 如果定时任务线程已经启动，先停止它
        if _task_thread_started and _task_thread and _task_thread.is_alive():
            print_warning("【应用启动】检测到旧的定时任务线程，将在重新加载时重启")
        
        # 启动新的定时任务线程
        try:
            from jobs import start_all_task
            print_info("【应用启动】正在启动定时任务...")
            _task_thread = threading.Thread(target=start_all_task, daemon=False, name="定时任务线程")
            _task_thread.start()
            _task_thread_started = True
            print_info("【应用启动】定时任务线程已启动")
        except Exception as e:
            print_warning(f"【应用启动】启动定时任务失败: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        if not job_arg:
            print_warning("【应用启动】未开启定时任务: -job 参数未设置为 True")
        if not enable_job_config:
            print_warning("【应用启动】未开启定时任务: server.enable_job 配置为 False")
    
    yield  # 应用运行期间
    
    # 关闭时执行
    if _task_thread_started:
        print_info("【应用关闭】定时任务线程将在应用关闭时自动停止")

app = FastAPI(
    title="WeRSS API",
    description=_WERSS_OPENAPI_DESCRIPTION.strip(),
    version=VERSION,
    docs_url="/api/docs",  # 指定文档路径
    redoc_url="/api/redoc",  # 指定Redoc路径
    # 指定OpenAPI schema路径
    openapi_url="/api/openapi.json",
    lifespan=lifespan,  # 使用新的 lifespan 事件处理器
    openapi_tags=[
        {
            "name": "认证",
            "description": "登录、Token、扫码绑定微信公众平台等",
        },
        {
            "name": "文章管理",
            "description": "文章列表（支持时间范围、标签筛选）、详情与维护",
        },
        {
            "name": "API Key 管理",
            "description": "API Key 的创建、轮换与调用日志（需登录）",
        },
    ],
    swagger_ui_parameters={
        "persistAuthorization": True,
        "withCredentials": True,
    },
)


def custom_openapi():
    """合并 OpenAPI：补充 API Key 安全方案，便于 Swagger 中展示。"""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    components = openapi_schema.setdefault("components", {})
    schemes = components.setdefault("securitySchemes", {})
    schemes.setdefault(
        "ApiKeyHeader",
        {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "WeRSS API Key（`werss_` 前缀）。与 JWT 二选一即可访问需登录接口。",
        },
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key 使用日志记录中间件
from core.middleware import ApiKeyLoggingMiddleware
app.add_middleware(ApiKeyLoggingMiddleware)

@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Version"] = VERSION
    response.headers["Server"] = cfg.get("app_name", "WeRSS")
    # 为静态资源和 index.html 添加缓存控制头
    path = request.url.path
    if path.startswith(("/assets/", "/static/")) or path == "/" or (not path.startswith("/api/") and not path.startswith("/files/")):
        # 开发环境禁用缓存，生产环境可以设置较长的缓存时间
        # 对于 index.html 和前端路由，必须禁用缓存，避免旧版本问题
        if path == "/" or (not path.startswith("/assets/") and not path.startswith("/static/")):
            # index.html 和前端路由：完全禁用缓存
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            # 添加 CSP 响应头，允许 Monaco Editor 从 CDN 加载资源
            # img-src 使用 https: 通配任意 HTTPS 图床，不在 CSP 中写死对象存储/部署域名
            # Cloudflare Web Analytics：beacon 脚本 + RUM 上报（见 cloudflare 文档 Web Analytics + CSP）
            # connect-src 需要包含开发环境的 API 地址
            csp_policy = (
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://static.cloudflareinsights.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "img-src 'self' data: blob: https: https://cdn.jsdelivr.net https://mmbiz.qpic.cn https://mmbiz.qlogo.cn https://mmecoa.qpic.cn https://wx.qlogo.cn https://thirdwx.qlogo.cn; "
                "connect-src 'self' http://localhost:8001 http://127.0.0.1:8001 http://localhost:5174 http://127.0.0.1:5174 https://cdn.jsdelivr.net https://cloudflareinsights.com; "
                "worker-src 'self' blob: https://cdn.jsdelivr.net; "
                "child-src 'self' blob: https://cdn.jsdelivr.net"
            )
            response.headers["Content-Security-Policy"] = csp_policy
        else:
            # /static/res/logo/* 是反向代理回源的图片，必须按响应实际状态决定缓存策略：
            # - 上游 200：短期缓存即可（apis/res.py 内部已按 1 小时落盘）
            # - 上游 4xx/5xx：禁止缓存，避免「盗链占位图」被浏览器顽固缓存到下个版本
            if path.startswith("/static/res/logo/"):
                if 200 <= response.status_code < 300:
                    response.headers["Cache-Control"] = "public, max-age=3600"
                else:
                    response.headers["Cache-Control"] = "no-store"
            else:
                # 普通静态资源：可以长缓存（带 hash 文件名，配合 immutable 安全）
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response
# 创建API路由分组
api_router = APIRouter(prefix=f"{API_BASE}")
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(article_router)
api_router.include_router(wx_router)
api_router.include_router(config_router)
api_router.include_router(task_router)
api_router.include_router(fetch_task_router)
api_router.include_router(notify_task_router)
api_router.include_router(system_task_router)
api_router.include_router(sys_info_router)
api_router.include_router(tags_router)
api_router.include_router(article_tag_router)
api_router.include_router(export_router)
api_router.include_router(tools_router)
api_router.include_router(github_router)
api_router.include_router(dashboard_router)
api_router.include_router(api_key_router)
api_router.include_router(tag_cluster_router)
api_router.include_router(hot_topics_router)

# 添加独立的健康检查端点（用于 Docker healthcheck）
# /api/health：compose healthcheck、负载均衡探活常用
# /api/v1/sys/version：带版本信息的探活（不随 API_BASE 变化）
@app.get("/api/health", tags=["健康检查"], include_in_schema=False)
async def health_check():
    from fastapi.responses import JSONResponse
    return JSONResponse({"status": "ok"})


@app.get("/api/v1/sys/version", tags=["健康检查"], include_in_schema=False)
async def health_check_version():
    """健康检查端点，返回版本信息"""
    try:
        from apis.ver import API_VERSION
        from core.config import VERSION as CORE_VERSION
        from fastapi.responses import JSONResponse
        return JSONResponse({
            'api_version': API_VERSION,
            'core_version': CORE_VERSION,
            'status': 'running'
        })
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={'error': str(e), 'status': 'error'}
        )

# 资源反向代理路由（处理 /static/res/logo/ 路径）
# 注意：resource_router 只处理 /static/res/logo/ 路径，其他 /static/ 路径由静态文件服务处理
resource_router = APIRouter(prefix="/static")
resource_router.include_router(res_router)  # res_router 的 prefix 是 /res，所以完整路径是 /static/res/logo/{path:path}
feeds_router = APIRouter()
feeds_router.include_router(rss_router)
feeds_router.include_router(feed_router)
# 注册API路由分组
app.include_router(api_router)
app.include_router(mcp_router)
app.include_router(resource_router)  # 处理 /static/res/logo/ 路径
app.include_router(feeds_router)

# 静态文件服务（支持 HEAD 方法，用于 wx_qrcode.png 等文件）
# ⚠️ 关键：静态文件挂载必须在 API 路由之后，但在 catch-all 路由之前
# FastAPI 的路由匹配顺序：include_router > mount > 普通路由
from starlette.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from core.res.avatar import files_dir

# 静态文件目录路径
static_dir = os.path.join(os.path.dirname(__file__), "static")

# 1. 挂载 assets 目录（前端构建后的 JS/CSS 文件）
# 注意：必须在 /static 之前挂载，避免路径冲突
assets_dir = os.path.join(static_dir, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# 2. 挂载 static 目录（后端静态资源，如 logo.svg 等）
# 注意：在 resource_router 之后挂载，这样 /static/res/logo/ 会被 resource_router 处理
# 而其他 /static/ 路径（如 /static/wx_qrcode.png）会被静态文件服务处理
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 3. 用户上传文件服务（保留，因为这是业务功能，不是前端静态文件）
app.mount("/files", StaticFiles(directory=files_dir), name="files")

# ⚠️ 关键：SPA 应用的兜底路由 - 必须在所有 mount 之后定义
# 这个路由会捕获所有未匹配的路径，返回 index.html，让 React Router 接管路由
@app.get("/", tags=['默认'], include_in_schema=False)
async def serve_root(request: Request):
    """处理根路由 - 返回前端页面"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # 如果前端文件不存在，返回API信息
        return JSONResponse({
            "name": "WeRSS API",
            "version": VERSION,
            "status": "running",
            "docs": f"{request.base_url}api/docs",
            "message": u"前端文件未找到，请先构建前端"
        })

@app.get("/{catchall:path}", tags=['默认'], include_in_schema=False)
@app.head("/{catchall:path}", tags=['默认'], include_in_schema=False)
async def serve_react_app(request: Request, catchall: str):
    """
    捕获所有未匹配的路由 - SPA应用兜底路由
    解决 React Router 在刷新页面时的 404 问题，避免递归循环
    """
    # 1. 跳过 API 路径（这些应该由 API 路由处理）
    if catchall.startswith("api/"):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": u"API路径不存在",
                "api_docs": f"{request.base_url}api/docs"
            }
        )
    
    # 2. 跳过静态文件路径（这些应该由 StaticFiles 处理）
    # 如果这些路径到达这里，说明静态文件不存在，返回 404
    if catchall.startswith("static/") or catchall.startswith("files/") or catchall.startswith("assets/"):
        return Response(status_code=404)
    
    # 3. 对于所有其他路径（前端路由），返回 index.html
    # 让 React Router 在客户端处理路由
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": u"前端文件未找到，请先构建前端",
                "api_docs": f"{request.base_url}api/docs"
            }
        )
