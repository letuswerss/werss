# 热点发现

## 1. 功能目标

从最近 N 天的科技文章中自动发现热点主题，将多篇相关文章聚合为一个热点话题，供用户了解当前科技趋势。

## 2. 适用场景

- 了解最近几天科技领域发生了哪些重要事件
- 从文章聚合的角度发现主题，而非按标签聚合
- 每天早上自动运行，用户查看当日热点简报

## 3. 核心对象

| 对象 | 说明 |
|------|------|
| `HotTopicRun` | 热点发现任务的执行记录 |
| `HotTopic` | 热点主题实体 |
| `HotTopicArticle` | 热点主题与文章的关联 |

## 4. 数据流 / 工作流程

```
定时任务触发（每天 9:00，可配置） 或 手动触发
        ↓
从 Article 表拉取近 N 天文章（带标签）
        ↓
调用 LLM（OpenAI 兼容 API）对文章进行事件级聚类
        ↓
解析 LLM 返回结果，存储 HotTopic + HotTopicArticle
        ↓
用户在 /hot-topics 页面查看热点列表
```

### 4.1 时间窗口

- 默认 3 天（配置项 `hot_topics.window_days`）
- 可通过 `hot_topics.cron` 配置定时任务触发时间（默认 `0 9 * * *`）

### 4.2 与标签聚类的区别

| | 标签聚类（Tag Cluster） | 热点发现（Hot Topic） |
|---|---|---|
| **聚合对象** | 标签（Tag） | 文章（Article） |
| **聚合依据** | embedding 相似度 + n-gram 相似度 | 文章内容/语义相关性 |
| **目的** | 将相近的标签标准化 | 发现最近发生的事件主题 |
| **数据来源** | 所有标签 | 近期文章 |

## 5. 主要能力

### 5.1 手动触发

- Web UI：点击 `/hot-topics` 页面的"重新分析"按钮
- API：`POST /api/v1/wx/hot-topics/rebuild`（**需要登录**，`Authorization: Bearer <access_token>`）

### 5.2 查看历史结果

- API：`GET /api/v1/wx/hot-topics/recent` - 获取最近一次成功的热点发现结果（**无需登录**）
- 包含：`run_id`, `window_days`, `model_name`, `created_at`, `topics[]`
- 每个 topic 包含：`id`, `topic_name`, `summary`, `signals`, `article_count`, `article_ids`, `representative_titles`
- 指定某次 run 详情：`GET /api/v1/wx/hot-topics/runs/{run_id}`（**需要登录**）

### 5.3 定时任务

- 由 `jobs/hot_topics_job.py` 在 `start_all_task()` 中注册到 `TaskScheduler`（与采集等任务同一调度器）
- 进程需以 **`main.py -job True` 且配置 `server.enable_job: true`** 启动，才会在 [web.py 生命周期](../../web.py) 里拉起定时任务线程；否则**不会**自动跑 cron，仅可依赖手动触发
- 默认每天 9:00 执行（`hot_topics.cron`，默认 `0 9 * * *`）
- 需要配置 `openai.api_key`（或环境变量 `OPENAI_API_KEY`）；未配置时 **不会注册** 热点定时任务（仅警告日志）

## 6. 关键配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `hot_topics.enabled` | 是否启用热点发现 | true |
| `hot_topics.cron` | 定时任务 cron 表达式 | `0 9 * * *` |
| `hot_topics.window_days` | 时间窗口（天数） | 3 |
| `openai.api_key` | AI API Key | - |
| `openai.base_url` | API Base URL | https://api.openai.com/v1 |
| `openai.model` | 模型名称 | gpt-4o |

## 7. 关联页面与 API

- **Web UI：** `/hot-topics`（热点发现页面）
- **API：**
  - `GET /api/v1/wx/hot-topics/recent` - 获取最近热点结果
  - `GET /api/v1/wx/hot-topics/skill-brief` - **供外接撰写智能体 / Skill**：在最新一次成功 run 上，**每个**热点附带前 N 篇（默认 3 篇）参考文章，含标题、链接、公众号名与**可选正文**（**需登录**；Query：`articles_per_topic`、`include_content`、`max_content_chars`）
  - `POST /api/v1/wx/hot-topics/rebuild` - 手动触发热点发现
  - `GET /api/v1/wx/hot-topics/runs/{run_id}` - 获取指定 run 详情

### 7.1 每日拉取后送给撰写 Skill 的推荐流程

1. 保证当天已有成功热点：依赖 **定时任务**（`-job True` + `hot_topics.cron`）或定时调用 **`POST /rebuild`**。  
2. 定时（如 cron）调用 **`GET /api/v1/wx/hot-topics/skill-brief?articles_per_topic=3`**，带登录 Token。  
3. 解析 `data.topics[]`：每个元素含 `topic_name`、`summary`、`signals`、`reference_articles`（3 篇的 `title`/`url`/`content` 等），整段 JSON 交给你侧的文章生成 Skill/流水线。  
4. 若正文过大，可加 **`max_content_chars=8000`** 或设 **`include_content=false`** 仅用标题+链接。

仓库内示例脚本见 **`scripts/fetch_hot_topics_skill_brief.sh`**（需自行填入 `BASE_URL`、账号密码或已有 Token）。


## 8. 常见问题 / 限制

- **无文章数据：** 若近 N 天没有文章，热点发现返回空结果
- **API Key 未配置：** 定时任务注册时会警告，但不会报错
- **执行时间较长：** LLM 调用和解析可能需要几分钟，前端有倒计时展示

## 9. 相关文件

```
core/hot_topics/service.py      # 热点发现核心逻辑
core/hot_topics/prompt.py      # LLM 聚类 prompt
core/hot_topics/parser.py      # LLM 返回结果解析
core/hot_topics/repository.py  # 数据库操作
core/models/hot_topics.py      # HotTopic 模型
core/models/hot_topic_runs.py  # HotTopicRun 模型
core/models/hot_topic_articles.py # HotTopicArticle 模型
jobs/hot_topics_job.py         # 定时任务注册
apis/hot_topics.py            # API 路由
web_ui/src/views/HotTopics.tsx # 热点发现页面
```
