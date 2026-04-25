# 系统核心流程

本文按步骤串起 WeRSS 的主干数据流，便于对照代码与配置。

---

## 1. 公众号订阅 -> 文章采集 -> 文章入库

本流程面向私有自用场景。请仅在有权访问、保存和使用相关内容的范围内启用采集能力，避免公开批量抓取、缓存或再分发第三方内容。

**入口：**
- Web UI：`/subscriptions` 页面添加公众号订阅
- API：`POST /api/v1/wx/subscriptions`

**采集方式（配置项 `gather.content_mode`）：**
- `web`：使用 Playwright 浏览器驱动（`driver/wxarticle.py`）抓取
- `api`：使用 `WxGather` 类（`core/wx/`）调用微信 API 提取
- `app`：App 采集模式

**定时采集：**
- 由 `jobs/mps.py` 中的定时任务触发
- 调度器 `TaskScheduler` 按 cron 表达式执行 `start_job()`
- 采集时检查微信 Session 是否有效（`check_session_valid()`）

**文章入库：**
- 文章存入 `Article` 表（`core/models/article.py`）
- 关键字段：`id`, `mp_id`, `title`, `url`, `publish_time`, `content`, `digest`, `pic_url`
- 状态：`status = DATA_STATUS.ACTIVE`（1=正常，2=禁用，3=已删除）

---

## 2. 文章 -> 标签提取 -> 标签管理 / 标签筛选

**标签来源有两种：**

### 2a. AI 自动提取
- 调用 `core/tag_extractor.py` 的 `TagExtractor.extract_with_ai()`
- 通过 OpenAI 兼容 API（配置项 `openai.api_key` / `openai.base_url` / `openai.model`）
- Prompt 模板见 `core/tag_extractor.py` 中的 `DEFAULT_TAG_EXTRACT_PROMPT_TEMPLATE`
- 默认每次提取 5 个标签（配置项 `article_tag.max_tags`）
- 提取时优先匹配用户自定义标签（`is_custom=True` 的标签）

### 2b. 手动创建标签
- 通过 API：`POST /api/v1/wx/tags`
- 或 Web UI：`/tags` 页面

**标签管理：**
- API：`GET /api/v1/wx/tags`（分页列表，含近 3 天文章数统计）
- `PUT /api/v1/wx/tags/{tag_id}` 更新标签
- `DELETE /api/v1/wx/tags?tag_ids=id1,id2` 批量删除

**标签筛选（filtered tag）：**
- 标签通过 `is_filter` 字段区分是否用于筛选
- 文章列表 API 支持按标签筛选（`tag_id` / `tag_ids` 参数）

---

## 3. 标签 -> 标签聚类

**功能：**
- 将语义相近的标签聚合为标签聚类（Tag Cluster）
- 位于 `core/tag_cluster.py` 的 `rebuild_tag_clusters()` 函数

**算法：**
- 基于 embedding 相似度 + 字符 n-gram 相似度的加权组合
- 建图后稀疏化（每个节点保留 top-k 边），再用连通分量生成簇
- 配置项：`TAG_CLUSTER_SIMILARITY_THRESHOLD`（默认 0.78）、`TAG_CLUSTER_MAX_SIMILAR_TAGS`、`TAG_CLUSTER_GRAPH_TOP_K`

**与标签本身的区别：**
- 标签（Tag）= 文章的关键词
- 标签聚类（Tag Cluster）= 多个相近标签的聚合

**入口：**
- API：`POST /api/v1/wx/tag-clusters/rebuild` 触发重建
- 定时任务：默认每天执行

---

## 4. 最近文章 -> 热点发现

**功能：**
- 从最近 N 天的文章中发现科技热点主题
- 位于 `core/hot_topics/service.py` 的 `run_discovery()`

**时间窗口：**
- 默认 3 天（配置项 `hot_topics.window_days`）
- 可通过 `hot_topics.cron` 配置定时任务触发时间

**数据流：**
1. 从 `Article` 表拉取近 N 天文章（带标签）
2. 调用 LLM 对文章进行事件级聚类
3. 解析 LLM 返回结果，存入 `HotTopic` 表
4. 关联文章到 `HotTopicArticle` 表

**与标签聚类的区别：**
- 标签聚类 = **标签的聚合**（embedding 相似）
- 热点发现 = **文章的聚合**（内容/时间相关）

**入口：**
- Web UI：`/hot-topics` 页面
- API：`GET /api/v1/wx/hot-topics/recent` 获取最近结果
- API：`POST /api/v1/wx/hot-topics/rebuild` 手动触发

---

## 5. 文章 -> RSS 输出

**功能：**
- 将文章摘要输出为标准 RSS 2.0 订阅源；如需全文输出，应先确认内容授权、使用范围和分发对象

**实现：**
- `core/rss.py` 生成 RSS XML
- API：`GET /rss/{feed_id}.xml`

**数据来源：**
- 对应一个 `subscription`（订阅）
- 关联 `feed` 表（`core/models/feed.py`）

---

## 6. 文章 -> 消息任务 -> Webhook 通知

**功能：**
- 定时汇总公众号文章，通过 Webhook 发送通知

**实现：**
- `jobs/taskmsg.py` 获取消息任务
- `jobs/mps.py` 的 `do_job()` / `do_job_all_feeds()` 执行采集和汇总
- `jobs/webhook.py` 的 `web_hook()` 发送 Webhook 请求
- `core/lax.py` 的 `TemplateParser` 渲染消息模板

**通知渠道：**
- 支持钉钉、企业微信、飞书、Webhook

**入口：**
- Web UI：`/message-tasks` 页面
- API：`POST /api/v1/wx/message-tasks`

---

## 7. 文章 -> 导出 / 图片转存

**导出功能：**
- 支持 PDF、Markdown 格式，建议仅用于个人归档或已授权内容
- API：`POST /api/v1/wx/export`

**图片转存：**
- 使用 MinIO 对象存储（配置项 `minio.`），默认不建议转存第三方图片；确有授权或私有归档需求时再开启
- `core/storage/` 实现转存逻辑

**入口：**
- Web UI：`/export/records` 页面

---

## 流程关系图

```
mp (公众号)
  │
  ├── subscription (订阅) ─── feed (RSS) ─── RSS 输出
  │
  └── article (文章)
        │
        ├── tag (标签) ─── tag cluster (标签聚类)
        │
        └── hot_topic (热点) ← 文章聚合

message_task (消息任务) → Webhook 通知
article → export / 图片转存
```
