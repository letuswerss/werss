# 贡献指南

本文档面向准备给 `werss` 提交文档、前端、后端、采集链路或任务调度改动的开发者。目标很简单：

- 先理解你要改的那一层
- 用最小改动解决问题
- 在提交前做对口验证
- 不把旧文档、旧路径、旧认知继续带回仓库

## 1. 开始之前先做什么

第一次接触仓库，建议先读这一组文档：

1. [README.md](../README.md)
2. [overview.md](./overview.md)
3. [concepts.md](./concepts.md)
4. [QUICK_START.md](./QUICK_START.md)

如果你改的是特定模块，再补读对应文档：

- 后端接口或数据流：
  [backend-structure.md](./dev/backend-structure.md)、
  [data-model-overview.md](./dev/data-model-overview.md)
- 前端页面或交互：
  [frontend-structure.md](./dev/frontend-structure.md)
- 调度器、采集任务、保留策略：
  [jobs-and-schedulers.md](./dev/jobs-and-schedulers.md)
- 配置项、环境变量、部署差异：
  [configuration-and-precedence.md](./dev/configuration-and-precedence.md)、
  [DEPLOYMENT.md](./DEPLOYMENT.md)
- 标签、热点、消息任务这类业务能力：
  [tag-system.md](./features/tag-system.md)、
  [hot-topics.md](./features/hot-topics.md)、
  [rss-and-message-tasks.md](./features/rss-and-message-tasks.md)

## 2. 先确认你改的是什么

提交前先把改动归类。不要一边改页面，一边顺手改接口语义，再顺手改数据库字段。

常见改动类型：

- 文档补全或纠错
- 前端页面与交互
- 后端 API
- 采集逻辑
- 定时任务
- 数据模型
- 部署与配置

不同类型的改动，验证方式不一样。`服务能启动` 不等于 `功能改对了`。

## 3. 分支与提交建议

建议一个功能或一个修复用一个独立分支：

```bash
git checkout -b feature/your-change
```

不要把这些无关事情混在同一轮里：

- 文档重写
- 接口行为变更
- UI 调整
- 配置语义变更
- 大规模重构

如果你确实必须跨层修改，至少要在 PR 里把边界讲清楚。

## 4. 改动前的基本原则

- 小改动优先，不要一口气做大重构
- 优先复用已有模块和现有模式
- 不要把复杂业务塞进路由层
- 不要把页面逻辑散落到多个临时组件里
- 配置改动必须同步更新示例和文档
- 当前代码是第一事实来源，不要按旧 README 或旧印象改

这个仓库历史演进比较多，最常见的问题不是“不会写”，而是：

- 以为系统还是旧结构
- 以为某个接口或页面还是旧行为
- 文档已经更新，但代码没有对应修改
- 代码改了，文档还在讲上一版

## 5. 提交前要做什么验证

下面这张表是最实用的最小验证清单。

| 改动类型 | 最少要验证什么 |
| --- | --- |
| 文档 | 路径没写错、没有继续引用不存在的页面/接口、内容与当前代码一致 |
| 前端 | 页面能打开、路由能进入、相关接口正常、`pnpm build` 能过 |
| 后端 | 服务能启动、`/api/health` 正常、你改的接口能通、异常返回合理 |
| 采集逻辑 | 采集链路能走通、失败时有日志或显式错误、不会静默吞掉问题 |
| 定时任务 | `-job True` 下能正常注册和执行、调度器状态正常 |
| 数据模型 | 初始化或迁移流程能走通，相关查询和写入不报错 |
| 部署与配置 | 环境变量优先级、默认值、Docker/本地差异都已核对 |

### 文档改动

至少确认：

- 引用的文档和代码路径存在
- 文字描述和当前实现一致
- 没有残留旧页面名、旧 API 路径、旧模型名
- 如果改了 `docs-site`，运行文档校验

推荐执行：

```bash
cd docs-site
npm run check:docs
```

### 前端改动

至少确认：

- 对应页面能正常打开
- 路由可进入
- 接口调用没有明显回归
- 构建通过

推荐执行：

```bash
cd web_ui
pnpm build
```

### 后端改动

至少确认：

- 服务能启动
- `/api/health` 返回正常
- 你改的接口能通
- 异常输入不会直接 500

常用启动方式：

```bash
python main.py -init True
python main.py -job False -init False
```

### 采集和任务调度改动

至少确认：

- `-job True` 下任务会注册
- 调度器状态正常
- 登录态失效、接口异常时不会静默失败
- 关键日志可用于排查

建议补查：

- [jobs-and-schedulers.md](./dev/jobs-and-schedulers.md)
- [workflows.md](./workflows.md)

## 6. 文档和代码要一起维护

如果你改了以下任何内容，通常都应该同步更新文档：

- 页面入口
- 路由
- API 路径
- 配置项
- 数据模型语义
- 定时任务行为
- 采集链路

最常见的问题不是“没写新文档”，而是：

- 旧文档没删
- 页面已经变了，文档还在讲上一版
- 新功能做了，但 README 和文档导航完全看不出来

## 7. 提交说明怎么写

不要写这种提交信息：

```bash
git commit -m "fix"
git commit -m "update"
```

至少要说明为什么改：

```bash
git commit -m "Clarify hot topic docs and align links with current docs site routing"
```

如果你在本仓库直接提交代码，建议遵守仓库里的 Lore 提交规范。重点不是形式感，而是把这些讲清楚：

- 为什么要改
- 有什么外部约束
- 放弃过什么方案
- 验证了什么
- 还没验证什么

## 8. Pull Request 里建议写什么

一个可读的 PR，至少应包含：

- 改动目的
- 改了哪些模块
- 如何验证
- 已知风险或未覆盖点

如果改的是界面，最好附截图或录屏。  
如果改的是接口，最好附请求示例或返回结构说明。  
如果改的是文档站，最好说明：

- 改了哪些入口
- 有无新增路由
- `npm run check:docs` 是否通过

## 9. 什么情况下应该先开 Issue

这些情况建议先开 Issue 或先对齐方案，再开始动手：

- 新增较大功能
- 改动现有接口语义
- 改动数据库字段语义
- 引入新依赖
- 要动采集主链路
- 要改部署方式或默认配置行为

如果只是小修复、文档补全、错链修正、明显 bug，一般可以直接做。

## 10. 对外协作时最重要的一点

请始终以当前代码为准。

不要按这些东西脑补仓库结构：

- 旧 README
- 旧截图
- 外部文章
- 以前的使用记忆

这个项目已经不算小了。真正高质量的贡献，不是“改得多”，而是：

- 理解边界
- 改动克制
- 验证到位
- 文档同步
