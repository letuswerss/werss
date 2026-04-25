# WeRSS 开发环境快速开始

本文目标只有一个：尽快把本仓库在本地跑起来。不穷举所有部署形态，只写当前代码里**最稳、最常用**的开发路径。

## 1. 你会启动什么

本地开发通常分成两部分：

- 后端：FastAPI，默认端口 `8001`
- 前端：React + Vite，默认端口 `5174`

最常见的访问地址：

- 前端开发页：`http://localhost:5174`
- 后端接口：`http://localhost:8001`
- API 文档：`http://localhost:8001/api/docs`
- 健康检查：`http://localhost:8001/api/health`

## 2. 前置条件

至少准备这些：

- Python 3.11+
- Node.js 20+
- 一个可用的数据库
  开发阶段 SQLite、PostgreSQL 都能用；若要尽量贴近生产、把整条链路跑通，建议用 PostgreSQL。

如果你要跑微信采集和浏览器抓取，还需要本机能正常运行 Playwright 依赖。

## 3. 最快启动方式

如果你只想先把前后端都拉起来，直接用仓库自带脚本：

```bash
./start_dev.sh
```

这个脚本会尝试：

- 检查环境
- 启动后端
- 启动前端
- 打开开发地址

适合第一次快速看页面。

## 4. 推荐的手动开发方式

如果你是开发者，建议手动分开启动，这样排查更清楚。

### 4.1 Python 环境

推荐用 `uv`：

```bash
uv venv
source .venv/bin/activate
uv sync
```

如果你不用 `uv`，也可以自己用 `venv + pip`，但当前仓库已经有 `pyproject.toml` 和 `uv.lock`，优先按这一套来。

### 4.2 初始化数据库

首次运行建议先做初始化：

```bash
python main.py -init True
```

这一步会确保数据库表存在，并执行初始化逻辑。

### 4.3 启动后端

```bash
python main.py -job True -init False
```

说明：

- `-job True`
  表示同时启用后台任务和调度器
- `-init False`
  表示这次启动不再重复初始化

如果你只想调 API，不想跑后台任务，也可以把 `-job` 关掉：

```bash
python main.py -job False -init False
```

### 4.4 启动前端

```bash
cd web_ui
pnpm install
pnpm dev
```

前端默认监听：

- `http://localhost:5174`

## 5. 构建生产前端资源

如果你改了前端，并且想把构建产物同步进后端 `static/`，执行：

```bash
cd web_ui
pnpm build:deploy
```

这一步不是开发调试必需，但如果你要验证“后端直接托管前端资源”的形态，就需要它。

## 6. 配置从哪里来

开发时最常见的配置来源有这些：

- `.env`
- `config.yaml`
- 环境变量
- 数据库中的配置覆盖

建议起步时先看：

- `.env.example`
- `config.example.yaml`
- [配置与优先级](./dev/configuration-and-precedence.md)

最容易踩的坑是：

- 你以为改了 `config.yaml`
- 实际被环境变量或数据库覆盖了

## 7. 典型开发链路

### 只看页面

```bash
./start_dev.sh
```

### 改后端接口

```bash
source .venv/bin/activate
python main.py -job False -init False
```

然后用：

- `http://localhost:8001/api/docs`

直接验证接口。

### 改前端页面

```bash
cd web_ui
pnpm dev
```

配合后端一起跑即可。

### 改定时任务或采集链路

```bash
python main.py -job True -init False
```

因为不开 `job` 时，你根本看不到那部分真实行为。

## 8. Docker 开发什么时候用

仓库提供了：

- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-compose.app-only.yml`

Docker 更适合：

- 统一环境
- 接近部署环境
- 带 Postgres / MinIO 一起联调

但如果你只是改页面或接口，优先本地直跑，反馈更快。

完整部署细节请看：

- [DEPLOYMENT.md](./DEPLOYMENT.md)

## 9. 常见问题

### 后端能起，前端打不开

优先检查：

- 是否在 `web_ui/` 下执行了 `pnpm install`
- `5174` 端口是否被占用

### 页面打开了，但接口都报错

优先检查：

- 后端是否已经启动
- `8001` 端口是否可访问
- 登录态是否存在

### 采集相关功能不工作

优先检查：

- 是否用 `-job True` 启动
- 微信登录状态是否有效
- Playwright 依赖是否正常

### 改了前端但后端托管页面没变化

因为开发模式和后端静态资源不是同一套产物。要让后端托管页面更新，需要执行：

```bash
cd web_ui
pnpm build:deploy
```

## 10. 建议阅读顺序

启动成功后，建议继续看：

- [overview.md](./overview.md)
- [workflows.md](./workflows.md)
- [backend-structure.md](./dev/backend-structure.md)
- [frontend-structure.md](./dev/frontend-structure.md)
