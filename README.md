<div align="center">

<img src="https://raw.githubusercontent.com/letuswerss/werss/main/web_ui/public/logo.svg" alt="WeRSS Logo" width="100" height="100">

# WeRSS - 自托管微信公众号内容聚合与AI分析系统

![Version](https://img.shields.io/badge/version-1.1.5-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![GitHub Stars](https://img.shields.io/github/stars/letuswerss/werss?style=social)
![GitHub Forks](https://img.shields.io/github/forks/letuswerss/werss?style=social)

**面向个人私有自托管场景的微信公众号内容整理、订阅、标签与热点分析系统**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [配置说明](#-配置说明) • [API 文档](#-api-文档) • [开发指南](#-开发指南) • [更新日志](#-更新日志) • [项目维护](#项目维护)

</div>

---

## 项目维护

**项目维护：** 当前版本的日常运维工作，包括 Issue / PR 处理、文档更新、版本整理和发布说明维护，都在持续收敛。也欢迎通过 Issue、PR 参与维护与共建。

---

## 项目简介

WeRSS 是一个面向个人私有自托管场景的微信公众号内容整理与分析系统。它提供文章订阅管理、摘要 RSS 输出、标签整理、热点追踪、消息通知和后台管理能力，适合作为个人信息处理工具使用，**不建议部署为公开内容聚合、全文转载或对外分发服务，法律责任及后果自负！** 也不要问问什么原作者删库跑路了，希望你好我好大家好。

### 合规与使用声明

本项目仅提供自托管的软件工具和技术实现，不提供、销售或代运营任何第三方内容服务，也不代表项目维护者主动建立或发布特定公众号订阅关系。订阅源、采集方式、采集频率、访问凭据、数据保存范围、对外展示和再分发行为均由部署者或最终用户自行配置和管理；用户应仅在其有权访问、保存和使用相关内容的范围内使用本项目。

部署或使用本项目时，使用者应自行遵守微信公众平台、腾讯及其他相关平台的服务协议、开发者规则、robots/反爬策略、知识产权规则、个人信息保护要求以及所在地适用法律法规。**不得将本项目用于绕过登录、验证码、访问控制或其他技术保护措施，不得用于批量抓取未授权内容、侵犯版权或将第三方内容用于未经许可的商业分发。**

本项目中出现的“微信”“微信公众号”等名称仅用于描述兼容对象和技术场景，不表示本项目与相关权利方存在授权、合作、关联或背书关系。项目维护者不对具体部署场景的合法性、合规性或第三方权利风险作出保证；如使用者将系统用于公网服务、团队协作、商业用途或内容再传播，应在上线前自行完成法务、隐私和版权评估，并根据权利方请求及时删除、屏蔽或停止处理相关内容。

建议的低风险使用方式：仅私有部署、启用登录认证、不提供真实内容演示、默认关闭正文采集、RSS 全文输出、图片转存和导出能力；收到权利方或平台通知后，应及时删除相关内容并停止对应处理。

### 技术栈

**后端：**
- **FastAPI** - 现代化的 Python Web 框架
- **SQLAlchemy** - Python ORM 框架
- **Playwright** - 浏览器自动化
- **APScheduler** - 定时任务调度

**前端：**
- **React 18** - UI 框架
- **TypeScript** - 类型系统
- **Vite** - 构建工具
- **Tailwind CSS** - 实用优先的 CSS 框架
- **Radix UI / shadcn/ui** - 组件库
- **React Router v6** - 路由管理
- **Zustand** - 状态管理
- **Axios** - HTTP 客户端

### 核心能力

- 🔄 **文章采集**：支持 `web / api / app` 多种采集模式
- 📰 **RSS 输出**：将文章摘要整理为标准 RSS 订阅源，可按需开启全文模式
- 🏷️ **标签体系**：支持手动管理标签，并支持基于 OpenAI 兼容接口的 AI 自动提取
- 🔥 **热点发现**：从最近几天文章中聚合科技热点主题
- 📤 **内容导出**：支持 PDF、Markdown 等导出方式，默认关闭
- 🗂️ **存储控制**：支持 MinIO 对象存储、图片转存开关和文章保留策略，默认不转存第三方图片
- 🔔 **消息通知**：支持钉钉、企业微信、飞书和自定义 Webhook
- 🔐 **权限控制**：提供用户认证与 API Key 管理
- ⏰ **任务调度**：支持定时采集、自动补全、热点分析和后台任务管理

### 系统能力图

```text
公众号订阅 -> 定时采集 -> 文章入库
                             ↓
             标签提取（手动 / AI） <- 公众号信息
                             ↓
             标签聚类 <- 标签管理 <- 标签筛选
                             ↓
             热点发现 <- 近期文章
                             ↓
             RSS 输出 / 消息推送 / 导出存储
```

---

## 界面预览

### 数据概览
<div align="center">
  <img src="https://raw.githubusercontent.com/letuswerss/werss/main/images/dashboard.png" alt="数据概览（浅色主题）" width="800"/>
  <br/>
  <img src="https://raw.githubusercontent.com/letuswerss/werss/main/images/dashboard-dark.png" alt="数据概览（深色主题）" width="800"/>
</div>

### 热点追踪
<div align="center">
  <img src="https://raw.githubusercontent.com/letuswerss/werss/main/images/hot-topics.png" alt="热点追踪" width="800"/>
</div>

### 文章列表
<div align="center">
  <img src="https://raw.githubusercontent.com/letuswerss/werss/main/images/articlelist.png" alt="文章列表" width="800"/>
</div>

### RSS 订阅
<div align="center">
  <img src="https://raw.githubusercontent.com/letuswerss/werss/main/images/rss.png" alt="RSS 订阅" width="800"/>
</div>

---

## 功能特性

### 文章管理

- 自动采集微信公众号文章
- 支持多种采集模式（`web / api / app`）
- 文章内容自动提取和清理
- 文章搜索和筛选
- 文章标签管理与筛选
- 支持 AI 过滤低价值文章

### RSS 订阅

- 标准 RSS 2.0 格式输出
- 支持全文 / 摘要模式
- 自定义 RSS 标题、描述、封面
- 支持 CDATA 格式
- 分页支持

### 标签系统

- 手动标签管理
- AI 自动标签提取
  - 当前仅支持基于 OpenAI 兼容接口的 AI 提取
  - 可接入 DeepSeek、OpenAI、Qwen 等兼容服务
  - 优先提取公司名称、产品名称、技术名称等具体实体
  - 对 Qwen3 模型自动关闭思考模式，直接返回可解析结果
- 基于公众号的自动标签关联
- 标签统计和分析
- 智能标签自动创建

### 热点发现

- 从最近 N 天文章中自动发现热点主题
- 将多篇相关文章聚合为“事件型主题”
- 提供热点摘要、信号词和关联文章列表
- 支持前端手动触发与定时任务自动分析

### 导出与存储

- PDF 导出（需启用）
- Markdown 导出（需启用）
- 多选导出支持
- MinIO 对象存储支持
- 文章图片自动下载和上传
- 图片 URL 自动替换为 MinIO 链接
- 支持是否转存文章图片的业务开关

### 通知系统

- 钉钉 Webhook 通知
- 企业微信 Webhook 通知
- 飞书 Webhook 通知
- 自定义 Webhook 通知
- 授权二维码过期通知
- 消息订阅模板（支持单个公众号和多公众号汇总）

### 消息订阅模板

系统支持通过消息任务定时汇总公众号文章，并支持自定义消息模板。

#### 模板类型

**1. 单个公众号模板**

适用于单个公众号的消息推送，可用变量如下：

- `{{feed.mp_name}}` - 公众号名称
- `{{articles}}` - 文章列表
- `{{article.title}}` - 文章标题
- `{{article.url}}` - 文章链接
- `{{article.publish_time}}` - 发布时间
- `{{article.description}}` - 文章描述
- `{{article.pic_url}}` - 封面图 URL

**示例模板：**

```jinja2
### {{feed.mp_name}} 订阅消息：
{% if articles %}
{% for article in articles %}
- [**{{ article.title }}**]({{article.url}}) ({{ article.publish_time }})
{% endfor %}
{% else %}
- 暂无文章
{% endif %}
```

**2. 多个公众号汇总模板（推荐）**

适用于汇总多个公众号的文章，可用变量如下：

- `{{feeds_with_articles}}` - 公众号及文章列表（数组）
- `{{item.feed.mp_name}}` - 公众号名称
- `{{item.articles}}` - 该公众号的文章列表
- `{{total_articles}}` - 总文章数
- `{{feeds_count}}` - 公众号数量
- `{{task.name}}` - 任务名称
- `{{now}}` - 当前时间

**默认汇总模板：**

```jinja2
# 每日订阅汇总

{% for item in feeds_with_articles %}
## {{ item.feed.mp_name }}

{% for article in item.articles %}
- [**{{ article.title }}**]({{ article.url }}){% if article.publish_time %} ({{ article.publish_time }}){% endif %}
{% endfor %}

{% endfor %}

---
共 {{ total_articles }} 篇文章，来自 {{ feeds_count }} 个公众号
```

**自定义汇总模板示例：**

```jinja2
# 每日订阅汇总

{% for item in feeds_with_articles %}
### {{ item.feed.mp_name }} 订阅消息：

{% for article in item.articles %}
- [**{{ article.title }}**]({{ article.url }}) ({{ article.publish_time }})
{% endfor %}

{% endfor %}

---
共 {{ total_articles }} 篇文章，来自 {{ feeds_count }} 个公众号
```

#### 模板语法

系统使用 Jinja2 风格模板语法，支持：

- **变量输出**：`{{ variable }}`
- **条件判断**：`{% if condition %}...{% endif %}`
- **循环遍历**：`{% for item in items %}...{% endfor %}`
- **点号访问**：`{{ item.feed.mp_name }}`（访问嵌套属性）

#### 模板选择逻辑

- 如果自定义模板中包含 `feeds_with_articles` 变量，系统会按汇总模式渲染
- 如果自定义模板中不包含 `feeds_with_articles`，系统会回退到默认汇总模板
- 单个公众号模板仅适用于单个公众号的消息推送场景

#### 支持的通知平台

- ✅ **飞书**：支持富文本（post）和文本格式，自动降级
- ✅ **钉钉**：支持 Markdown 格式
- ✅ **企业微信**：支持 Markdown 格式
- ✅ **自定义 Webhook**：支持 JSON 格式

#### 使用建议

1. **多公众号汇总**：优先使用包含 `feeds_with_articles` 的模板，一次汇总多个公众号内容
2. **单个公众号推送**：单个公众号模板更适合做定向订阅通知
3. **模板测试**：可在消息任务中先使用“测试”功能预览渲染结果
4. **Markdown 展示**：模板支持 Markdown，适合输出结构化通知内容

### 其他功能

- 用户认证和权限管理
- API Key 管理
- 系统配置管理
- 定时任务管理
- 系统信息监控
- 数据统计面板

---

## 快速开始

### 环境要求

**后端：**
- Python 3.11 或更高版本
- 数据库：SQLite / MySQL / PostgreSQL
- 浏览器：Firefox / Chromium / WebKit（用于 Playwright）

**前端：**
- Node.js 18 或更高版本
- 包管理器：`pnpm`（推荐）或 `npm`

### 方式一：一键启动开发环境（推荐）

```bash
# 克隆项目
git clone https://github.com/letuswerss/werss.git
cd werss

# 运行一键启动脚本
chmod +x start_dev.sh
./start_dev.sh
```

启动后访问：

- 前端界面：`http://localhost:5174`
- 后端 API：`http://localhost:8001`
- API 文档：`http://localhost:8001/api/docs`

### 方式二：手动安装

#### 1. 安装系统依赖

**Ubuntu / Debian：**

```bash
sudo apt-get update
sudo apt-get install -y \
    wget git build-essential zlib1g-dev \
    libgdbm-dev libnss3-dev libssl-dev libreadline-dev \
    libffi-dev libsqlite3-dev procps
```

**macOS：**

```bash
brew install python@3.11
```

#### 2. 创建虚拟环境

**使用 uv（推荐，更快）：**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
```

**使用传统方式：**

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装 Python 依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 4. 安装 Playwright 浏览器

```bash
playwright install firefox
```

#### 5. 配置环境

```bash
cp config.example.yaml config.yaml
```

首次运行至少需要：

```bash
export WERSS_USERNAME=admin
export WERSS_PASSWORD=your_password
export DB=sqlite:///data/db.db
```

#### 6. 初始化数据库

```bash
python main.py -init True
```

#### 7. 启动后端服务

```bash
python main.py -job True -init False
```

#### 8. 前端开发（可选）

```bash
cd web_ui
pnpm install
pnpm dev
```

前端服务启动后访问：`http://localhost:5174`

### 方式三：Docker 部署

#### 完整栈（默认）

```bash
cp .env.example .env
docker compose up -d
```

访问：

- 前端界面：`http://localhost:8001`
- API 文档：`http://localhost:8001/api/docs`

#### 已有外部数据库 / 对象存储

```bash
docker compose -f docker-compose.app-only.yml up -d --build
```

#### Docker Compose 开发环境

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

完整部署说明见 [部署指南](https://letuswerss.github.io/werss/docs/DEPLOYMENT)。

---

## 配置说明

### 配置文件

项目使用 `config.yaml` 进行配置，首次运行请从模板复制：

```bash
cp config.example.yaml config.yaml
```

### 环境变量

项目支持用环境变量覆盖配置文件中的设置，且环境变量优先级更高：

```bash
# 数据库配置
export DB=postgresql://user:password@localhost:5432/werss_db

# 服务器配置
export PORT=8001
export DEBUG=False
export AUTO_RELOAD=False

# 用户认证（首次运行）
export WERSS_USERNAME=admin
export WERSS_PASSWORD=your_password

# 定时任务
export ENABLE_JOB=True
export THREADS=2

# 文章保留策略（可选）
# export ARTICLE_RETENTION_ENABLED=true
# export ARTICLE_RETENTION_DAYS=7
# export ARTICLE_RETENTION_BASIS=created_at

# MinIO 可用时是否转存公众号相关图片；保守默认 false
# export MINIO_STORE_ARTICLE_IMAGES=false

# RSS 配置
export RSS_BASE_URL=https://your-domain.com/
export RSS_TITLE=我的RSS订阅
export RSS_DESCRIPTION=微信公众号内容分析系统

# 通知配置
export DINGDING_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
export WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
export FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# AI 标签提取（可选）
export OPENAI_API_KEY=sk-xxx
export OPENAI_BASE_URL=https://api.deepseek.com
export OPENAI_MODEL=deepseek-chat
```

### 主要配置项说明

#### 数据库配置

```yaml
# SQLite（默认）
db: sqlite:///data/db.db

# PostgreSQL
db: postgresql://username:password@host:5432/database

# MySQL
db: mysql+pymysql://username:password@host:3306/database?charset=utf8mb4
```

#### RSS 配置

```yaml
rss:
  base_url: https://your-domain.com/
  local: false
  title: 我的RSS订阅
  description: 微信公众号内容分析系统
  full_context: false
  add_cover: false
  page_size: 10
```

#### 采集配置

```yaml
gather:
  content: false
  model: app
  content_auto_check: false
  content_auto_interval: 59
  browser_type: firefox
```

#### 标签配置

```yaml
article_tag:
  auto_assign_by_mp: true
  auto_extract: false
  extract_method: ai
  max_tags: 5
  ai:
    auto_create: true
```

#### OpenAI 兼容 API 配置（AI 标签提取）

当前版本的自动标签提取仅支持 OpenAI 兼容接口。你可以接入 DeepSeek、OpenAI、Qwen 等兼容服务，代码侧统一走同一套 AI 提取链路。

```yaml
openai:
  api_key: sk-xxx
  base_url: https://api.deepseek.com
  model: deepseek-chat
```

**常见兼容服务示例：**

- **DeepSeek**：`https://api.deepseek.com`
- **OpenAI**：`https://api.openai.com/v1`
- **Qwen3**：`https://dashscope.aliyuncs.com/compatible-mode/v1`

#### MinIO 配置（可选）

```yaml
minio:
  enabled: false
  endpoint: "localhost:9000"
  access_key: "minioadmin"
  secret_key: "minioadmin"
  bucket: "articles"
  secure: false
  public_url: "http://localhost:9000"
```

更多配置细节请参考：

- [配置优先级](https://letuswerss.github.io/werss/docs/dev/configuration-and-precedence)
- [导出与存储](https://letuswerss.github.io/werss/docs/features/export-and-storage)
- [设置与运维](https://letuswerss.github.io/werss/docs/features/settings-and-ops)

---

## API 文档

启动服务后，可以通过以下地址访问 API 文档：

- **Swagger UI**: `http://localhost:8001/api/docs`
- **ReDoc**: `http://localhost:8001/api/redoc`
- **OpenAPI Schema**: `http://localhost:8001/api/openapi.json`

接口支持使用 JWT（`Authorization: Bearer <token>`）或 API Key（`X-API-Key: werss_xxxx`）鉴权。

### 主要 API 端点（节选）

#### 认证

- `POST /api/v1/wx/auth/token` - OAuth2 密码模式获取 JWT
- `POST /api/v1/wx/auth/login` - 用户登录
- `GET /api/v1/wx/auth/verify` - 校验 Token

#### API Key

- `GET /api/v1/wx/api-keys` - 列表
- `POST /api/v1/wx/api-keys` - 创建
- `POST /api/v1/wx/api-keys/{id}/regenerate` - 轮换密钥

#### 公众号

- `GET /api/v1/wx/mps` - 公众号列表
- `GET /api/v1/wx/mps/{mp_id}` - 详情

#### 文章

- `GET /api/v1/wx/articles` - 文章列表
- `POST /api/v1/wx/articles` - 复杂筛选查询
- `GET /api/v1/wx/articles/{id}` - 文章详情

#### 热点

- `GET /api/v1/wx/hot-topics/recent` - 最近一次热点结果（可匿名）
- `GET /api/v1/wx/hot-topics/skill-brief?articles_per_topic=3` - 每热点附带前 N 篇参考文章（需登录，供外接撰写 Skill；详见 `docs/features/hot-topics.md`）
- `POST /api/v1/wx/hot-topics/rebuild` - 手动触发热点发现

#### RSS / Feed

- `GET /rss`
- `GET /rss/{feed_id}`
- `GET /feed/{feed_id}.xml`

更细的字段说明与示例见 [文章查询 API](https://letuswerss.github.io/werss/docs/ARTICLE_QUERY_API)。

---

## 开发指南

### 项目结构

```text
werss/
├── apis/              # API 路由层
├── core/              # 核心业务逻辑
├── jobs/              # 定时任务
├── driver/            # 浏览器驱动（Playwright）
├── web_ui/            # 前端 React 应用
├── docs/              # 项目文档
├── main.py            # 应用入口
├── web.py             # FastAPI 应用定义
├── config.example.yaml
└── requirements.txt
```

### 开发环境设置

更细的开发说明请看：

- [快速开始](https://letuswerss.github.io/werss/docs/QUICK_START)
- [架构概览](https://letuswerss.github.io/werss/docs/dev/architecture-overview)
- [后端结构](https://letuswerss.github.io/werss/docs/dev/backend-structure)
- [前端结构](https://letuswerss.github.io/werss/docs/dev/frontend-structure)
- [任务与调度](https://letuswerss.github.io/werss/docs/dev/jobs-and-schedulers)

### 添加新功能

1. **添加新 API**
   - 在 `apis/` 目录下创建新文件
   - 在 `web.py` 中注册路由
2. **修改数据库模型**
   - 在 `core/models/` 下修改模型
   - 重新运行初始化或迁移流程
3. **添加定时任务**
   - 在 `jobs/` 下创建任务文件
   - 接入调度入口
4. **新增前端页面**
   - 在 `web_ui/src/views/` 创建页面
   - 在路由中接入

### 代码规范

- 遵循 Python PEP 8 代码规范
- 使用类型提示（Type Hints）
- 前后端修改都应以当前代码为准
- 文档改动同步更新，不要留旧路径和旧说明

---

## 更新日志

### v1.1.5

**内容分析与运维增强**
- 新增热点发现链路，支持从近期文章中聚合事件型热点
- 新增热点 API、运行记录和前端热点页
- 文档站上线，README 文档入口统一切到线上文档站
- 增加文章保留策略、MinIO 图片转存控制、API Key 管理、公众号信息更新等后台能力

### v1.1.4

**部署与配置整理**
- 补强 Docker Compose、Traefik、环境变量和部署说明
- 增加文章保留和对象存储相关配置
- AI 标签提取、设置页和后台能力进一步完善

### v1.1.3 及更早阶段

**基础能力成型**
- 标签聚类能力逐步完善
- 修复 MCP 支持相关问题
- 形成公众号采集、RSS 输出、标签管理、消息任务、后台管理这些基础能力
- 前后端分离结构和任务调度框架基本定型

这里只显示最近 3 次更新，更多版本说明见 [开发日志](https://letuswerss.github.io/werss/docs/dev/development-log)。

---

## 贡献指南

欢迎提交代码、文档或问题反馈。建议按以下流程协作：

1. [Fork 本项目](https://github.com/letuswerss/werss/fork)
2. 创建功能分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. [开启 Pull Request](https://github.com/letuswerss/werss/pulls)

详细协作规范见：

- [贡献指南](https://letuswerss.github.io/werss/docs/CONTRIBUTING)
- [开发日志](https://letuswerss.github.io/werss/docs/dev/development-log)

---

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

## 致谢

本项目在开发过程中参考和借鉴了以下开源项目，在此致谢：

- [we-mp-rss](https://github.com/letuswerss/we-mp-rss)
- [wewe-rss](https://github.com/cooderl/wewe-rss)
- [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)

感谢这些项目的开发者和贡献者。

---

## 支持

如有问题、建议或使用反馈，可通过以下方式联系：

如需技术合作、联合共建或定制开发，也欢迎通过仓库 Issue 或 PR 先说明背景与需求。
如果你希望围绕数据采集、标签分析或热点发现能力展开合作，可以在沟通中附上使用场景与预期目标，便于进一步对接。

- [提交 Issue](https://github.com/letuswerss/werss/issues)
- [发送 Pull Request](https://github.com/letuswerss/werss/pulls)
- [查看线上文档](https://letuswerss.github.io/werss)

---

<div align="center">

**如果这个项目对你有帮助，欢迎点个 Star**

[![Star History Chart](https://api.star-history.com/svg?repos=letuswerss/werss&type=Date)](https://www.star-history.com/#letuswerss/werss&Date)

Maintained by WeRSS contributors

</div>
