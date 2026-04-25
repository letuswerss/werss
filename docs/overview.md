# WeRSS 是什么

WeRSS 是一套面向**个人私有自托管**场景的微信公众号内容整理与分析系统：管理订阅来源，按配置获取文章信息，再提供摘要 RSS、标签、热点、消息通知与后台管理等能力。

## 合规与使用声明

本文档与仓库仅作**技术说明**，本项目仅提供自托管的软件工具和技术实现，不提供、销售或代运营任何第三方内容服务，也不代表项目维护者主动建立或发布特定公众号订阅关系。订阅源、采集方式、采集频率、访问凭据、数据保存范围、对外展示和再分发行为均由部署者或最终用户自行配置和管理；用户应仅在其有权访问、保存和使用相关内容的范围内使用本项目。

部署或使用本项目时，使用者应自行遵守微信公众平台、腾讯及其他相关平台的服务协议、开发者规则、robots/反爬策略、知识产权规则、个人信息保护要求以及所在地适用法律法规。不得将本项目用于绕过登录、验证码、访问控制或其他技术保护措施，不得用于批量抓取未授权内容、侵犯版权或将第三方内容用于未经许可的商业分发。

本项目中出现的“微信”“微信公众号”“腾讯”等名称仅用于描述兼容对象和技术场景，不表示本项目与相关权利方存在授权、合作、关联或背书关系。项目维护者不对具体部署场景的合法性、合规性或第三方权利风险作出保证；如使用者将系统用于公网服务、团队协作、商业用途或内容再传播，应在上线前自行完成法务、隐私和版权评估，并根据权利方请求及时删除、屏蔽或停止处理相关内容。

建议的低风险使用方式：
- 仅私有部署并启用登录认证，不提供匿名访问或真实内容演示
- 默认关闭正文采集、RSS 全文输出、图片转存和导出能力
- 不收费，不代他人部署为内容聚合站，不主动帮助他人分发第三方内容
- 收到平台或权利方通知后，及时删除相关内容并停止对应处理

## 核心能力

| 能力 | 说明 |
|------|------|
| 文章采集 | 支持按配置获取公众号文章信息，正文采集默认关闭 |
| RSS 输出 | 将文章摘要整理为标准 RSS 2.0 订阅源，全文输出需显式开启 |
| 标签提取 | 支持手动标签和基于 OpenAI 兼容接口的 AI 自动提取 |
| 标签聚类 | 基于 embedding 将标签按语义聚合 |
| 热点发现 | 从近期文章中发现科技热点主题 |
| 消息任务 | 支持钉钉、企业微信、飞书、Webhook 通知 |
| 导出存储 | 支持 PDF、Markdown 导出和 MinIO 图片转存，均建议按需开启 |

## 系统组成

```
werss/
├── apis/          # HTTP API 路由层
├── core/          # 核心业务逻辑、数据模型、配置
├── jobs/          # 定时任务（采集、清理、消息推送）
├── driver/        # Playwright 浏览器驱动
└── web_ui/        # React 前端
    ├── src/views/ # 页面组件
    ├── src/api/   # 前端 API 调用封装
    └── src/router/# 路由配置
```

## 核心数据流

```
公众号订阅 → 定时采集 → 文章入库
                              ↓
              标签提取（手动/AI）← 公众号信息
                              ↓
              标签聚类 ← 标签管理 ← 标签筛选
                              ↓
              热点发现 ← 文章列表
                              ↓
              RSS输出 / 消息推送 / 导出
```

## 已有的能力 vs 规划中的能力

**已有：**
- 文章采集（web/api/app）
- RSS 输出
- 标签系统（手动 + AI 提取）
- 标签聚类（基于 embedding）
- 热点发现
- 消息任务（Webhook 通知）
- 导出（PDF/Markdown）
- MinIO 图片转存

**规划中（未实现）：**
- 基于 GLiNER 的轻量化标签提取
- 微信内容自动生成
- 社区共建计划

---

## 谁应该看什么

| 角色 | 入口文档 |
|------|---------|
| 第一次接触项目 | 先看 `docs/overview.md`，再看 `docs/concepts.md` |
| 部署、运维 | `docs/DEPLOYMENT.md`、`docs/QUICK_START.md` |
| 后端、前端 | `docs/dev/architecture-overview.md`、`docs/dev/backend-structure.md` |
| 算法、大模型相关 | `docs/concepts.md`、`docs/features/tag-system.md`、`docs/features/hot-topics.md` |
| 主要用 Web 界面 | `docs/ui/articles.md`、`docs/ui/subscriptions.md` |

---

## 快速开始

**本地开发：**

```bash
# 一键启动
./start_dev.sh

# 访问
# 前端: http://localhost:5174
# 后端: http://localhost:8001
# API文档: http://localhost:8001/api/docs
```

**Docker 部署：**

```bash
cp .env.example .env
docker compose up -d
# 访问: http://localhost:8001
```

详细部署说明见 [docs/DEPLOYMENT.md](DEPLOYMENT.md)。

---

## 文档导航

### 第 1 层 - 导航层
- [README.md](../README.md)（仓库入口）
- [docs/DEPLOYMENT.md](./DEPLOYMENT.md)
- [docs/QUICK_START.md](./QUICK_START.md)

### 第 2 层 - 认知层
- [docs/overview.md](./overview.md)
- [docs/concepts.md](./concepts.md)
- [docs/workflows.md](./workflows.md)

### 第 3 层 - 功能层
- [docs/features/article-collection.md](./features/article-collection.md)
- [docs/features/tag-system.md](./features/tag-system.md)
- [docs/features/hot-topics.md](./features/hot-topics.md)
- [docs/features/rss-and-message-tasks.md](./features/rss-and-message-tasks.md)
- [docs/features/export-and-storage.md](./features/export-and-storage.md)

### 第 4 层 - UI 层
- [docs/ui/articles.md](./ui/articles.md)
- [docs/ui/subscriptions.md](./ui/subscriptions.md)
- [docs/ui/settings.md](./ui/settings.md)
- [docs/ui/tags.md](./ui/tags.md)
- [docs/ui/tag-clusters.md](./ui/tag-clusters.md)
- [docs/ui/hot-topics.md](./ui/hot-topics.md)
- [docs/ui/message-tasks.md](./ui/message-tasks.md)

### 第 5 层 - 开发层
- [docs/dev/architecture-overview.md](./dev/architecture-overview.md)
- [docs/dev/backend-structure.md](./dev/backend-structure.md)
- [docs/dev/frontend-structure.md](./dev/frontend-structure.md)
- [docs/dev/configuration-and-precedence.md](./dev/configuration-and-precedence.md)
- [docs/dev/jobs-and-schedulers.md](./dev/jobs-and-schedulers.md)
