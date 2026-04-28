# syntax=docker/dockerfile:1.4
# BuildKit：DOCKER_BUILDKIT=1 docker compose build（或默认已开启）以使用 RUN --mount=type=cache

# 多阶段构建：第一阶段 - 前端构建
FROM --platform=$BUILDPLATFORM node:20.18.0-slim AS frontend-builder

# 设置工作目录
WORKDIR /app

# 安装 pnpm
RUN npm install -g pnpm

# 复制前端依赖文件
COPY web_ui/package.json web_ui/pnpm-lock.yaml* web_ui/

# 安装前端依赖（BuildKit 缓存 pnpm store，加速重复构建）
WORKDIR /app/web_ui
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

# 复制前端源代码
COPY web_ui/ .

# 构建前端
RUN pnpm build

# 多阶段构建：第二阶段 - Python 应用
FROM --platform=$BUILDPLATFORM python:3.11-slim

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai \
    PIP_DEFAULT_TIMEOUT=100

# 安装系统依赖（最小化，只安装运行时需要的）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# 设置工作目录
WORKDIR /app

# 复制依赖文件
# 注意：Dockerfile 使用 requirements.txt 安装依赖
# pyproject.toml 是项目元数据（用于 pip install -e . 或 uv pip install .）
# 但 Docker 构建时使用 requirements.txt，确保两者保持同步
COPY requirements.txt .

# 安装 uv 包管理器（用于快速安装 Python 依赖）
RUN pip install uv --no-cache-dir

# 安装 Python 依赖（缓存 wheel；仅 requirements 变更时重跑）
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt || \
    pip install -r requirements.txt

# 安装 Playwright 浏览器：放在「复制业务代码」之前，仅 requirements/浏览器类型变更才重跑本层。
# 注意：勿把浏览器装到 RUN --mount=type=cache 目录，否则缓存不会写入镜像层，运行时会缺浏览器。
ARG BROWSER_TYPE=firefox
ENV BROWSER_TYPE=${BROWSER_TYPE} \
    PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=300000
RUN export PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=300000 && \
    ( export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright && \
      python3 -m playwright install ${BROWSER_TYPE} --with-deps || \
      ( echo "npmmirror 失败，改用官方 CDN..." && \
        PLAYWRIGHT_DOWNLOAD_HOST=https://playwright.azureedge.net python3 -m playwright install ${BROWSER_TYPE} --with-deps ) \
    ) || (echo "Playwright 浏览器安装失败，将在运行时安装" && true)

# 复制后端代码（排除 web_ui，因为前端已经构建完成）
COPY config.example.yaml config.yaml
COPY apis/ apis/
COPY core/ core/
COPY driver/ driver/
COPY tools/ tools/
COPY jobs/ jobs/
COPY schemas/ schemas/
COPY migrations/ migrations/
COPY web.py .
COPY main.py .
COPY job.py .
COPY tool.py .
COPY init_sys.py .
COPY install.sh .
COPY start.sh .

# 从第一阶段复制前端构建产物
COPY --from=frontend-builder /app/web_ui/dist ./static

# 设置脚本权限
RUN chmod +x install.sh start.sh

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["bash", "start.sh"]
