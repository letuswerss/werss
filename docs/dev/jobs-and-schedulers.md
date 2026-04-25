# 定时任务与调度器

本文档解释 WeRSS 后端里哪些能力依赖调度器、任务是怎么注册的、手动触发和自动触发有什么区别。

## 1. 先看结论

当前 `jobs/` 不是一个“可有可无的后台附属品”，而是系统主链路的一部分。至少这些能力依赖它：

- 公众号定时采集
- 消息任务定时推送
- 缺正文文章补全文
- 文章保留策略清理
- 热点发现

如果你只跑 API、不跑 job，系统仍然能打开，但很多后台能力不会自动工作。

## 2. 任务总入口

[jobs/__init__.py](../../jobs/__init__.py) 当前非常薄，真正的主入口在 `jobs/mps.py` 及各注册函数里。

你应该重点看：

- [jobs/mps.py](../../jobs/mps.py)
- [jobs/article_retention.py](../../jobs/article_retention.py)
- [jobs/hot_topics_job.py](../../jobs/hot_topics_job.py)
- [jobs/fetch_no_article.py](../../jobs/fetch_no_article.py)

## 3. 调度器的角色

项目里用的是统一调度器思路：

- 用 `TaskScheduler` 注册 cron 任务
- 不同 job 共用同一个调度器实例或调度机制
- 任务状态会在系统信息和设置页显示

从使用方式上看，它负责两类事：

### 3.1 真正的 cron 定时任务

例如：

- 每隔一段时间抓一次公众号
- 每天固定时间清理旧文章
- 每天固定时间跑热点发现

### 3.2 持续后台队列

例如缺正文文章补全文，虽然不一定表现为显式 cron，但属于后台持续处理逻辑。

## 4. 公众号采集任务

最核心的任务仍然在 [jobs/mps.py](../../jobs/mps.py)。

它做的事不止“采文章”，还包括：

- 检查微信 Session 是否有效
- 根据配置计算抓取页数
- 手动执行指定公众号更新
- 在消息任务里复用采集逻辑
- 维护任务队列状态

几个重要点：

- 会先做 `check_session_valid()`
- 采集起始时间会参考控制台配置 `collect_start_date`
- 有频率限制，不允许过于频繁地刷新同一公众号

这意味着如果用户说“页面点刷新没反应”，不能只看前端，优先查：

- 微信是否仍然登录
- 上次刷新时间是否太近
- `server.enable_job` 和启动参数是否正确

## 5. 缺正文补全任务

[jobs/fetch_no_article.py](../../jobs/fetch_no_article.py) 负责把已经有元数据、但正文缺失的文章继续补全。

这个任务的意义很大，因为系统里的文章并不是一次性都能拿到完整内容：

- 初次采集可能只有标题、摘要、封面
- 后续需要补抓正文

如果标签提取、热点发现效果变差，常见原因不是 AI 模型，而是正文补全率低。

## 6. 消息任务调度

消息任务是“用户配置任务，系统按 cron 跑”的典型例子。

相关代码主要在：

- [apis/message_task.py](../../apis/message_task.py)
- [jobs/taskmsg.py](../../jobs/taskmsg.py)
- [jobs/mps.py](../../jobs/mps.py)

运行形态：

1. 用户在页面里创建 `MessageTask`
2. 写入 `message_tasks` 表
3. 调度器读取 `cron_exp`
4. 到点后执行
5. 任务会抓对应公众号的文章并通过 Webhook 发送

需要注意的一点：

页面上的“应用”或“刷新调度”动作不是装饰，它的目的是让新的任务配置真正进入调度器。

## 7. 文章保留清理

[jobs/article_retention.py](../../jobs/article_retention.py) 只负责“注册”清理任务，真正删除逻辑在 `core.article_retention`。

它会读取这些配置：

- `article.retention.enabled`
- `article.retention.cron`
- `article.retention.days`
- `article.retention.basis`

所以这里要分清两层：

- 是否启用和何时执行：`jobs/article_retention.py`
- 实际删哪些文章：`core/article_retention.py`

## 8. 热点发现任务

热点发现既可以手动触发，也可以定时触发。

相关代码主要在：

- [apis/hot_topics.py](../../apis/hot_topics.py)
- [jobs/hot_topics_job.py](../../jobs/hot_topics_job.py)
- `core.hot_topics.service`

推荐理解方式：

- API 负责暴露重建入口和结果查询
- job 负责定时调度
- core 负责真正的聚类与持久化

定时注册与 **进程启动方式** 有关：需 `main.py -job True` 且 `server.enable_job` 为 true，热点任务才会随 `start_all_task()` 注册；详见 [docs/features/hot-topics.md](../features/hot-topics.md) 第 5.3 节。

## 9. 手动触发和自动触发的区别

这点经常被误解。

### 手动触发

通常来自页面按钮或 API：

- 刷新一个订阅
- 手动跑一次热点发现
- 手动执行一个消息任务

特点：

- 可立即反馈结果
- 更适合局部重试

### 自动触发

来自调度器：

- 定时采集
- 定时清理
- 定时热点分析

特点：

- 依赖启动参数和调度器状态
- 更适合持续运行

同一个能力可能同时支持两者，但它们的入口代码不一定相同。

## 10. 线上排查时先看什么

如果用户说“任务没跑”，建议按这个顺序查：

1. 后端是否用 `-job True` 启动
2. 对应功能的配置是否启用
3. 调度器状态页是否显示在运行
4. 任务是否注册成功
5. 微信 Session 是否失效
6. 消息任务 / 热点任务本身是否有报错

## 11. 新增一个 job 的建议方式

不要直接把逻辑全写进 `jobs/`。

更稳的方式是：

1. 先把业务逻辑写进 `core/`
2. `jobs/` 里只保留调度和触发包装
3. 需要时再在 `apis/` 里提供手动触发入口

这样同一套能力才能被：

- 页面按钮复用
- 定时任务复用
- 测试代码复用

## 12. 最容易踩的坑

- 只加了 API，没有注册后台 job。
- 只改了 cron 表达式，没有确认调度器已重载。
- 把业务逻辑写死在任务函数里，导致无法手动复用。
- 忘了任务需要微信登录状态。
- 用户以为“保存配置”就会自动生效，实际上还需要刷新调度器。
