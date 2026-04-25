# 文章采集

## 1. 功能目标

在私有自用且有权访问相关内容的前提下，将公众号文章信息定时或手动写入 WeRSS 数据库，供后续的标签提取、RSS 输出、热点发现等功能使用。正文采集、历史批量抓取和内容补全应按需显式开启。

## 2. 适用场景

- 首次添加公众号后导入少量必要历史文章
- 定时增量采集已订阅公众号的新文章信息
- 文章内容被删除时重新抓取
- 采集失败时切换采集模式重试

## 3. 核心对象

| 对象 | 说明 |
|------|------|
| `Article` | 文章实体，`articles` 表 |
| `mp` | 公众号，`mps` 表 |
| `subscription` / `Feed` | 订阅（RSS 表现） |

## 4. 数据流 / 工作流程

```
用户添加公众号订阅
        ↓
公众号记录写入 mps 表（通过 faker_id 关联微信账号）
        ↓
定时任务触发采集（jobs/mps.py）
        ↓
┌──────────────────────────────────────────┐
│  gather.content_mode 配置决定采集方式：    │
│                                          │
│  web 模式 → Playwright 浏览器驱动         │
│              driver/wxarticle.py         │
│              (WXArticleFetcher 类)       │
│                                          │
│  api 模式 → WxGather + WX_API             │
│              core/wx/wx.py                │
│              driver/wx.py                │
│                                          │
│  app 模式 → App 采集                      │
└──────────────────────────────────────────┘
        ↓
采集回调 UpdateArticle() 写入 articles 表
        ↓
入库后字段：id, mp_id, title, url, publish_time,
           pic_url, description, content, digest
```

## 5. 主要能力

### 5.1 三种采集模式

**web 模式（默认）：**
- 使用 Playwright 浏览器模拟操作
- 位于 `driver/wxarticle.py` 的 `WXArticleFetcher` 类
- 支持提取阅读量、点赞量等统计数据
- 不应将该模式用于绕过登录、验证码、访问控制或平台技术保护措施

**api 模式：**
- 直接调用微信接口获取文章
- 位于 `driver/wx.py` 的 `Wx` 类和 `core/wx/wx.py`
- 依赖登录态（Session + Token）

**app 模式：**
- App 采集模式（未完全实现）

### 5.2 定时采集

- 调度器 `TaskScheduler`（`core/task.py`）按 cron 表达式执行
- `jobs/mps.py` 中的 `start_job()` 注册采集任务
- `check_session_valid()` 检查微信 Session 是否有效（登录状态 + cookie 剩余时间）

### 5.3 重新获取文章内容

- `POST /api/v1/wx/articles/{article_id}/fetch_content`
- 用于文章内容为空或被删除后重新抓取
- 支持 web / api 模式切换（配置项 `gather.content_mode`）

## 6. 关键配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `gather.content_mode` | 采集模式：web / api / app | web |
| `gather.content` | 是否采集正文内容 | false |
| `max_page` | 每次采集的页数 | 1 |
| `collect_start_date` | 首次采集的起始日期 | 2025-12-01 |
| `openai.api_key` | AI API Key（用于标签提取） | - |

## 7. 关联页面与 API

- **Web UI：** `/wechat/mp`（公众号详情）、`/subscriptions`（订阅管理）
- **API：**
  - `POST /api/v1/wx/mps` - 添加公众号
  - `GET /api/v1/wx/articles` - 文章列表
  - `POST /api/v1/wx/articles/{article_id}/fetch_content` - 重新获取内容
  - `DELETE /api/v1/wx/articles/clean` - 清理孤立文章
  - `DELETE /api/v1/wx/articles/clean_duplicate_articles` - 清理重复文章

## 8. 常见问题 / 限制

- **Session 失效：** 微信登录态过期会导致 api 模式失败，需重新扫码登录
- **文章被删除：** 返回 `DELETED`，系统自动将文章状态标记为已删除
- **采集频率：** 每天最多采集 `max_page` 页（默认 1 页），可在配置中调整
- **内容为空：** 部分文章正文需要单独获取（`fetch_content`），可能因上游访问策略或页面结构变化失败
- **合规边界：** 不建议公开运营、批量抓取未授权内容、缓存全文或帮助他人分发第三方内容

## 9. 相关文件

```
driver/wxarticle.py       # web 模式采集（Playwright）
driver/wx.py             # api 模式驱动
core/wx/wx.py           # WxGather 封装
core/wx/wx_api.py       # 微信 API 调用
jobs/mps.py             # 定时采集任务入口
jobs/article.py         # 文章更新回调
core/models/article.py  # Article 数据模型
core/models/feed.py     # Feed（订阅的 RSS 表现）
```
