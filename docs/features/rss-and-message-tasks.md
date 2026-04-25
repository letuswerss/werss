# RSS 与消息任务

## 1. 功能目标

RSS 和消息任务是 WeRSS 的两种信息推送机制：

- **RSS**：被动拉取，用户通过 RSS Reader 订阅公众号的 Feed，系统按需生成 XML/JSON
- **消息任务**：主动推送，用户配置 Webhook 和消息模板，系统按 Cron 表达式定时发送文章摘要到指定渠道

两者都围绕"文章数据"展开，但面向不同使用场景。

## 2. 适用场景

| 场景 | 使用 RSS | 使用消息任务 |
|---|---|---|
| 用户自行用 RSS Reader 订阅 | ✓ | |
| 定时推送到企业微信/钉钉/飞书群 | | ✓ |
| 按公众号隔离推送不同渠道 | | ✓ |
| 支持全文/摘要切换 | ✓ | ✓（模板控制） |
| 需要登录认证 | 可选 | 需要（消息任务需管理员配置） |

## 3. 核心对象

### 3.1 Feed（公众号订阅）

```python
class Feed:
    id: str          # 公众号 ID（mp_id）
    mp_name: str     # 公众号名称
    mp_intro: str   # 公众号简介
    mp_cover: str   # 公众号封面图
    status: int      # 1=启用，0=禁用
```

Feed 是 RSS 的基础单位，也是消息任务中指定推送范围的单位。

### 3.2 MessageTask（消息任务）

```python
class MessageTask:
    id: str              # 任务 ID（UUID）
    name: str             # 任务名称
    message_template: str  # 消息模板（支持占位符）
    web_hook_url: str    # Webhook 地址
    message_type: int    # 0=article, 其他扩展
    mps_id: str          # 关联的公众号 ID 列表（JSON 数组字符串）
    cron_exp: str        # Cron 表达式
    status: int          # 1=启用，0=禁用
```

## 4. RSS 工作流程

### 4.1 路由入口

```
GET /feed/mp/{mp_id}.rss   → RSS 2.0
GET /feed/mp/{mp_id}.atom  → ATOM
GET /feed/mp/{mp_id}.json  → JSON Feed
GET /feed/all.rss           → 全部订阅的 RSS（未指定 mp_id）
```

### 4.2 生成流程

```
请求到达 apis/rss.py get_mp_articles_source()
    │
    ├── 查询 Feed + Article 表
    │   - 指定 mp_id：仅该公众号文章
    │   - 无 mp_id：所有公众号文章
    │   - 支持 tag_id 筛选（按标签关联的订阅）
    │
    ├── 构建 rss_list：
    │   - id: 文章 ID
    │   - title: 文章标题
    │   - link: 文章链接（local=True 时为代理链接，否则为微信原文）
    │   - description: 摘要
    │   - content: 正文（full_context=True 时包含）
    │   - image: 封面图
    │   - mp_name: 公众号名称
    │   - updated: 发布时间
    │
    ├── 缓存文章内容到 data/cache/content/{article_id}.json
    │
    └── core/rss.py RSS.generate() 生成对应格式
        - rss/atom: XML
        - json: JSON
        - 支持 cdata、add_cover 等配置
```

### 4.3 RSS 配置

`config.yaml` 中的 RSS 相关配置：

```yaml
rss:
  base_url: ${RSS_BASE_URL:-}   # 填写真实域名，RSS 链接才正确
  local: ${RSS_LOCAL:-False}    # True=本地代理，False=微信原文
  full_context: ${RSS_FULL_CONTEXT:-False}  # True=全文；保守默认False，仅输出摘要
  add_cover: ${RSS_ADD_COVER:-False}  # True=添加封面 enclosure；保守默认False
  cdata: ${RSS_CDATA:-False}    # True=内容用 CDATA
  page_size: ${RSS_PAGE_SIZE:-10}  # 每页条数
```

### 4.4 本地代理模式

当 `rss.local=True` 时，文章链接指向 `${base_url}/rss/content/{article_id}`，该端点返回处理后的 HTML 页面（添加 `/static/res/logo/` 前缀到图片 URL）。

## 5. 消息任务工作流程

### 5.1 路由入口

消息任务通过 Web UI 管理（`/message-tasks`），API 在 `apis/message_task.py`：

```
GET    /message_tasks           → 列表
POST   /message_tasks           → 创建
PUT    /message_tasks/{id}      → 更新
DELETE /message_tasks/{id}     → 删除
POST   /message_tasks/{id}/run → 手动触发
GET    /message_tasks/{id}     → 详情
```

### 5.2 定时执行流程

```
APScheduler 触发 jobs/taskmsg.py
    │
    ├── 读取 MessageTask 表，筛选 status=1 的任务
    │
    ├── 对每个任务：
    │   ├── 解析 mps_id（JSON 数组），获取对应的公众号列表
    │   │
    │   ├── 查询这些公众号的最新文章
    │   │
    │   ├── 渲染 message_template
    │   │   支持占位符：{{title}}、{{link}}、{{description}}、{{content}} 等
    │   │
    │   └── 调用 core/notice/notice()
    │           │
    │           ├── 识别 Webhook 类型（企业微信/钉钉/飞书/custom）
    │           │
    │           └── 调用对应发送函数
    │               - send_wechat_message()
    │               - send_dingtalk_message()
    │               - send_feishu_message()
    │               - send_custom_message()
```

### 5.3 message_template 占位符

模板中可使用以下占位符（由 `core/content_format.py` 的 `format_content` 处理）：

| 占位符 | 说明 |
|---|---|
| `{{title}}` | 文章标题 |
| `{{link}}` | 文章链接 |
| `{{description}}` | 文章摘要 |
| `{{content}}` | 文章正文（HTML） |
| `{{mp_name}}` | 公众号名称 |
| `{{publish_time}}` | 发布时间 |

### 5.4 Webhook 类型自动识别

`core/notice/__init__.py notice()` 函数根据 Webhook URL 自动识别通知类型：

| Webhook URL 特征 | 类型 |
|---|---|
| `qyapi.weixin.qq.com` | 企业微信 |
| `oapi.dingtalk.com` | 钉钉 |
| `open.feishu.` 或 `feishu.cn` | 飞书 |
| 其他 | custom（直接 POST） |

## 6. RSS 与消息任务的边界与联系

### 6.1 边界

| 维度 | RSS | 消息任务 |
|---|---|---|
| 触发方式 | 用户主动拉取（RSS Reader） | 系统主动推送（Webhook） |
| 频次控制 | 无限制，用户自己控制 | 按 Cron 表达式，最小 1 分钟 |
| 目标用户 | 分散的 RSS Reader 用户 | 集中在企业群/通知渠道 |
| 内容控制 | 默认摘要，可显式开启全文 | 完全自定义模板 |
| 认证 | 可选（代码中被注释） | 需要管理员登录 |

### 6.2 联系

- 数据源相同：都从 `articles` 表查询数据
- 可按公众号隔离：RSS 按 `mp_id`，消息任务按 `mps_id`
- 都可以输出全文（RSS 用 `full_context`，消息任务模板中用 `{{content}}`），但公开或多人分发前应确认内容授权和使用边界

## 7. 关键配置

### 7.1 Webhook 内容格式

```yaml
webhook:
  content_format: ${WEBHOOK.CONTENT_FORMAT:-html}  # html/text/markdown
```

### 7.2 通知渠道配置

```yaml
notice:
  dingding: "${DINGDING_WEBHOOK}"
  wechat: "${WECHAT_WEBHOOK}"
  feishu: "${FEISHU_WEBHOOK}"
  custom: "${CUSTOM_WEBHOOK}"
```

## 8. 关联页面与 API

| 资源 | 页面 | API |
|---|---|---|
| RSS Feed | 文章列表页右上角 RSS 按钮 | `GET /feed/mp/{mp_id}.{format}` |
| 消息任务 | `/message-tasks` | `apis/message_task.py` |
| 消息任务执行 | 消息任务页"测试"/"执行"按钮 | `POST /message_tasks/{id}/run` |
| 调度器状态 | 设置页"定时抓取任务"卡片 | `GET /api/sys_info` |

## 9. 常见问题

### 9.1 RSS 链接打不开

检查 `config.yaml` 中 `rss.base_url` 是否为真实可访问的域名。本地开发时默认为请求的 `base_url`。

### 9.2 消息任务不执行

排查：
1. 调度器是否运行（设置页查看"调度器状态"）
2. 任务 `status` 是否为 1（启用）
3. `cron_exp` 是否正确
4. 进程是否以 `-job True` 启动

### 9.3 Webhook 发送失败

检查：
1. Webhook URL 是否正确
2. 网络是否能访问对应域名（企业微信/钉钉/飞书）
3. `notice_type` 是否与 URL 匹配
4. 消息内容是否超限（部分渠道有大小限制）

## 10. 相关文件

- `apis/rss.py` — RSS 路由
- `apis/message_task.py` — 消息任务 CRUD
- `core/rss.py` — RSS 生成器
- `core/notice/__init__.py` — 通知调度器
- `core/notice/wechat.py`、`dingtalk.py`、`feishu.py`、`custom.py` — 各渠道实现
- `jobs/taskmsg.py` — 定时任务执行逻辑
- `web_ui/src/views/MessageTaskList.tsx` — 消息任务页面
- `web_ui/src/views/ArticleListPage.tsx` — RSS 按钮入口
