# 后端结构

本文档面向要改后端 API、任务逻辑或数据流的开发者。目标是让你在读代码前先知道每一层该负责什么，避免把业务塞错地方。

## 1. 先建立整体心智

当前后端可以按 5 层来理解：

1. `main.py`
   进程入口，负责解析启动参数。
2. `web.py`
   FastAPI 应用装配，注册路由、中间件、静态资源和 SPA 兜底。
3. `apis/`
   HTTP 路由层，负责参数接收、权限校验、返回格式。
4. `core/`
   真正的业务逻辑、模型、配置、微信采集、对象存储、AI 处理。
5. `jobs/`
   定时任务与异步触发层，负责采集、补全文、消息推送、文章清理、热点发现。

如果一个改动同时涉及“接口行为”和“实际业务”，通常要同时看 `apis/` 和 `core/`，不要只改一层。

## 2. 入口文件

### `main.py`

`main.py` 不是业务入口，而是进程入口。它主要处理：

- 初始化数据库或系统资源
- 读取 `-job`、`-init` 之类的启动参数
- 启动 `uvicorn`

你通常不会在这里加业务代码。适合放在这里的只有：

- 启动参数
- 进程级初始化
- 启动模式切换

### `web.py`

`web.py` 是 HTTP 应用入口，职责非常集中：

- 创建 FastAPI 实例
- 注册所有 `apis/*` 路由
- 配置 OpenAPI 文档
- 配置认证、中间件、CORS
- 挂载 `/assets`、`/static`、`/files`
- 提供前端 SPA 兜底

如果你新增了一个 API 文件，但前端请求 404，第一件事就是检查 `web.py` 里是否 `include_router`。

## 3. 路由层：`apis/`

`apis/` 的职责是“把 HTTP 请求翻译成系统动作”，它不应该承载复杂业务。

当前主要模块如下：

- `auth.py`
  登录、令牌、用户身份相关。
- `article.py`
  文章列表、筛选、详情、删除、AI 过滤等。
- `mps.py`
  公众号搜索、订阅管理、手动刷新文章。
- `rss.py`
  RSS / Atom / JSON Feed 输出。
- `tags.py`
  标签 CRUD、测试提取、状态管理。
- `tag_clusters.py`
  标签聚类列表、详情、重建、导出、可视化概览。
- `hot_topics.py`
  科技热点列表、重建、运行记录查询。
- `message_task.py`
  消息任务 CRUD、手动执行。
- `config_management.py`
  控制台配置项的读写。
- `sys_info.py`
  系统资源、版本、调度器和微信登录状态。
- `api_key.py`
  API Key 管理和调用日志。
- `export.py`
  公众号和标签导入导出。

路由层应当做这些事：

- 解析 Query / Body / Path
- 认证和权限校验
- 调用 `core/` 或 `jobs/` 里的能力
- 统一返回 `success_response` / `error_response`

不应该做这些事：

- 写大段业务规则
- 直接堆复杂 SQL
- 在请求函数里维护长期状态

## 4. 业务层：`core/`

`core/` 是项目最重的一层，读代码时可以再拆成几类：

### 4.1 配置与基础设施

- `core/config.py`
  配置读取与优先级整合。
- `core/config_overrides.py`
  配置覆盖缓存。
- `core/db.py` / `core/database.py`
  数据库 session 与基础访问。

### 4.2 数据模型

- `core/models/*`
  SQLAlchemy 模型定义。

常用实体包括：

- `Feed`
  公众号订阅实体。
- `Article`
  文章实体。
- `Tags`
  标签实体。
- `ArticleTag`
  文章与标签关联。
- `MessageTask`
  消息任务。
- `ApiKey` / `ApiKeyLog`
  API 密钥和调用日志。
- `TagCluster*`
  标签聚类相关表。
- `HotTopic*`
  热点发现相关表。

### 4.3 微信采集与解析

- `core/wx/`
  微信侧查询和抓取逻辑。
- `driver/`
  Playwright / 浏览器驱动、登录状态、token。

### 4.4 AI 与内容处理

- `core/tag_extractor.py`
  标签提取。
- `core/tag_cluster.py`
  标签聚类重建。
- `core/article_filter.py`
  AI 文章过滤。
- `core/hot_topics/`
  热点发现。

### 4.5 资源与存储

- `core/res.py`
  头像与资源保存。
- `core/minio_*`
  对象存储能力。
- `core/article_retention.py`
  文章清理逻辑。

## 5. 任务层：`jobs/`

`jobs/` 负责“时间驱动”或“后台驱动”的动作，不是给前端直接调用的业务层。

当前关键任务包括：

- `jobs/mps.py`
  公众号文章采集、消息任务执行、调度器核心入口。
- `jobs/fetch_no_article.py`
  为缺正文的文章补全文。
- `jobs/article_retention.py`
  注册文章清理任务。
- `jobs/hot_topics_job.py`
  注册热点发现任务。
- `jobs/taskmsg.py`
  消息任务调度支持。
- `jobs/webhook.py`
  Webhook 推送。

如果某个能力既支持“页面按钮手动触发”又支持“定时触发”，通常页面会走 API，而 API 内部再调用 `jobs/` 或和 `jobs/` 共用同一套底层逻辑。

## 6. 一条真实链路怎么走

以“订阅管理页手动刷新一个公众号”为例：

1. 前端调用 `GET /api/v1/wx/mps/update/{mp_id}`
2. 路由在 [apis/mps.py](../../apis/mps.py) 做频率限制和基础校验
3. 内部通过 `WxGather` 拉取文章
4. 回调 `jobs/article.py` 里的 `UpdateArticle`
5. 文章写入 `Article` 表
6. 页面轮询或刷新后重新读订阅统计

再比如“热点发现”：

1. 前端访问 `/hot-topics`
2. 页面读取 `GET /api/v1/wx/hot-topics/recent`（无需登录）
3. 路由从 `HotTopicRun`、`HotTopic`、`HotTopicArticle` 取最新结果
4. 如果用户手动重建，则调用 `POST /api/v1/wx/hot-topics/rebuild`（需登录）
5. 后端进入 `core.hot_topics.service.run_discovery`

## 7. 常见改动应该落在哪

### 新增一个接口

落点：

- 新建或修改 `apis/*.py`
- 在 `web.py` 注册 router
- 需要时补 `core/` 业务逻辑

### 新增一个后台分析能力

落点：

- 业务逻辑写在 `core/`
- 如果需要定时执行，再补 `jobs/`
- 只在 `apis/` 暴露控制接口和结果查询

### 改配置项

落点：

- `core/config.py`
- `config.example.yaml`
- `.env.example`
- 若支持控制台覆盖，再看 `apis/config_management.py`

### 改页面展示字段

不要只改前端。

先确认：

- API 是否已经返回字段
- 模型是否有字段
- 后端是否正确序列化

## 8. 最容易踩的坑

- 把业务写在路由层，后面无法复用。
- 改了模型字段，没有同步任务层和导出层。
- 只改 `web_ui`，忘了后端接口返回结构不匹配。
- 只改 API，不看 `jobs/` 是否还有一份同逻辑。
- 修改配置项但不检查环境变量和数据库覆盖优先级。

## 9. 阅读顺序建议

如果你第一次接触这个后端，建议按这个顺序读：

1. [web.py](../../web.py)
2. [apis/article.py](../../apis/article.py)
3. [apis/mps.py](../../apis/mps.py)
4. [jobs/mps.py](../../jobs/mps.py)
5. [core/models](../../core/models/feed.py)
6. [core/config.py](../../core/config.py)

这样最容易把系统的主干看明白。
