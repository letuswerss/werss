# 系统架构概览

本文给一张总览图：WeRSS 分几层、数据怎样流动、新功能该落在哪。细节仍以各子模块文档为准。

## 1. 一句话架构

当前 WeRSS 可以概括成：

`React 管理台 + FastAPI 接口层 + Python 业务核心 + 定时任务系统 + 微信采集与对象存储能力`

它既不是「只爬网页」的脚本，也不是典型前后端分家的 SaaS，而是一套从采集、结构化、分析到分发的整体。

## 2. 系统分层

### 前端层

- 技术：React 18 + TypeScript + Vite
- 位置：`web_ui/`
- 职责：页面、路由、交互、调用后端 API

### 接口层

- 技术：FastAPI
- 位置：`web.py` + `apis/`
- 职责：HTTP 路由、认证、参数校验、统一响应

### 核心业务层

- 技术：Python 模块
- 位置：`core/`
- 职责：配置、模型、采集、标签提取、聚类、热点、通知、导出、对象存储

### 调度与后台任务层

- 技术：Python + `TaskScheduler` / APScheduler 思路
- 位置：`jobs/`
- 职责：定时采集、补全文、消息任务、文章清理、热点发现

### 资源与采集驱动层

- 技术：微信采集逻辑 + Playwright / 浏览器驱动 + 对象存储
- 位置：`driver/`、`core/wx/`、相关存储模块
- 职责：把外部内容拉进系统，并管理图片等资源

## 3. 目录到职责的映射

最重要的目录可以这样看：

- `main.py`
  进程入口和启动参数处理
- `web.py`
  FastAPI app 装配
- `apis/`
  路由和接口契约
- `core/`
  业务逻辑与模型
- `jobs/`
  定时任务
- `driver/`
  微信和浏览器驱动
- `web_ui/`
  React 管理台
- `docs/`
  项目文档

## 4. 一条主链路怎么流动

最核心的业务流可以简化为：

```text
公众号来源
  -> 订阅记录
  -> 文章采集
  -> 文章入库
  -> 标签提取 / AI 过滤
  -> 标签聚类 / 热点发现
  -> RSS / 消息任务 / 导出
```

这条链路解释了为什么项目会同时包含：

- 采集能力
- 标签能力
- 热点能力
- 推送能力

它们并不是互不相关的功能堆砌，而是同一条内容处理链上的不同环节。

## 5. 请求流和任务流要分开理解

### 请求流

用户操作页面时，大致路径是：

```text
浏览器
  -> React 页面
  -> /api/*
  -> apis/*.py
  -> core/*
  -> 数据库 / 存储 / 外部服务
```

### 任务流

后台自动运行时，大致路径是：

```text
调度器
  -> jobs/*.py
  -> core/*
  -> 数据库 / 微信 / Webhook / 存储
```

这两条流经常会落到同一个 `core` 能力上，但入口不一样。

## 6. 当前几个核心能力怎么落层

### 文章采集

- 页面入口：订阅管理、公众号管理
- 接口层：`apis/mps.py`
- 核心层：`core/wx/`
- 任务层：`jobs/mps.py`

### 文章工作台

- 页面入口：`/articles`
- 接口层：`apis/article.py`
- 核心层：文章模型、AI 过滤、标签提取等

### 标签与聚类

- 页面入口：`/tags`、`/tag-clusters`
- 接口层：`apis/tags.py`、`apis/tag_clusters.py`
- 核心层：`core/tag_extractor.py`、`core/tag_cluster.py`

### 热点发现

- 页面入口：`/hot-topics`
- 接口层：`apis/hot_topics.py`
- 核心层：`core.hot_topics.*`
- 任务层：`jobs/hot_topics_job.py`

### 消息任务

- 页面入口：`/message-tasks`
- 接口层：`apis/message_task.py`
- 任务层：`jobs/taskmsg.py`、`jobs/mps.py`
- 核心层：通知和模板渲染相关模块

## 7. 配置为什么是一个单独问题

这个项目的配置不是简单单源读取，而是多层覆盖：

- 示例配置文件
- 本地配置文件
- `.env`
- 数据库配置覆盖
- 运行时环境变量

所以配置是架构的一部分，而不是普通附属细节。

如果一个功能改动涉及开关、cron、模型名、存储策略，你就已经进入配置架构范围了。

## 8. 开发时该怎么定位改动层

### 改页面展示

先看 `web_ui/`

### 改接口行为

先看 `apis/`，再追到 `core/`

### 改后台调度

先看 `jobs/`

### 改数据结构

先看 `core/models/`

### 改运行配置

先看 `core/config.py` 以及配置相关文档

## 9. 这套架构最容易出的问题

- 路由层堆业务逻辑
- 同一能力在 API 和 job 里各写一份
- 配置改了但不清楚覆盖优先级
- 页面展示和真实接口返回长期漂移

所以整个文档系统才会强调一件事：

要始终以当前代码为准，而不是以过去的 README 或印象为准。

## 10. 建议继续阅读

如果你已经看懂这篇，继续读这些文档最有效：

- [backend-structure.md](./backend-structure.md)
- [frontend-structure.md](./frontend-structure.md)
- [jobs-and-schedulers.md](./jobs-and-schedulers.md)
- [data-model-overview.md](./data-model-overview.md)
- [workflows.md](../workflows.md)
