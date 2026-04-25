# 数据模型概述

本文档解释 WeRSS 当前最重要的数据实体、它们之间的关系，以及改字段时应该先想到什么。

## 1. 先抓主干

如果只记住一条主线，应该是：

`Feed(公众号订阅) -> Article(文章) -> Tag / ArticleTag(标签) -> TagCluster(标签聚类) -> HotTopic(热点主题)`

外围再挂：

- `MessageTask`
- `ApiKey`
- `ConfigManagement`
- `User`

## 2. 公众号与订阅

### Feed

[core/models/feed.py](../../core/models/feed.py)

`Feed` 是当前系统里最核心的“公众号入口实体”，字段包括：

- `id`
  主键，同时也是很多地方使用的 `mp_id`
- `mp_name`
  公众号名称
- `mp_cover`
  头像或封面
- `mp_intro`
  简介
- `status`
  启用状态
- `sync_time`
  同步时间
- `update_time`
  上次更新时间
- `faker_id`
  微信侧抓取和识别时使用的关联标识

需要注意：

- 前端通常把它叫“订阅”
- 文章表里 `Article.mp_id` 实际就是对 `Feed.id` 的引用语义

## 3. 文章

### Article

[core/models/article.py](../../core/models/article.py)

文章是系统里最重的实体，至少承担这些职责：

- RSS 输出的原始内容
- 标签提取的输入
- 热点发现的输入
- 消息任务推送的内容源

关键字段通常包括：

- `id`
  文章唯一标识
- `mp_id`
  所属公众号
- `title`
  标题
- `url`
  原文链接
- `description`
  摘要
- `content`
  正文
- `pic_url`
  封面图
- `publish_time`
  发布时间
- `created_at`
  入库时间
- `status`
  删除或禁用状态

几个关键点：

- `publish_time` 和 `created_at` 不是一回事
- 文章保留策略可按两者之一作为基准
- 有些文章初次入库时正文可能为空，后续由后台补全

## 4. 标签

### Tags

[core/models/tags.py](../../core/models/tags.py)

标签是文章的二次结构化层。关键字段包括：

- `id`
- `name`
- `cover`
- `intro`
- `status`
- `mps_id`
- `is_custom`
- `created_at`
- `updated_at`

这里有两个要点：

### `is_custom`

表示是否为用户手动定义标签。它很重要，因为：

- 手动标签常常代表业务偏好
- AI 提取时可能会优先参考

### `mps_id`

是标签和公众号维度关联的扩展字段，别把它理解成简单备注。

## 5. 文章与标签关系

### ArticleTag

[core/models/article_tags.py](../../core/models/article_tags.py)

这是典型的中间表，用来表达：

- 一篇文章可以有多个标签
- 一个标签可以关联多篇文章

很多页面上的“文章数量”“标签数量”都不是直接表字段，而是由这张表统计出来的。

如果你改标签删除逻辑，必须考虑 `ArticleTag` 是否需要联动清理。

## 6. 标签聚类相关实体

标签聚类不是只有一张表，当前至少包括：

- `TagCluster`
- `TagClusterMember`
- `TagClusterAlias`
- `TagEmbedding`
- `TagSimilarity`
- `TagProfile`

### TagCluster

[core/models/tag_clusters.py](../../core/models/tag_clusters.py)

关键字段：

- `id`
- `name`
- `description`
- `centroid_tag_id`
- `size`
- `cluster_version`

它代表的是“一个聚类结果快照中的一个簇”，不是永久不变的业务实体。

也就是说：

- 重建聚类后，簇可能重新分配
- `cluster_version` 很重要，不能忽略

## 7. 热点发现相关实体

热点发现是另一条分析链，不和标签聚类混为一谈。

### HotTopicRun

[core/models/hot_topic_runs.py](../../core/models/hot_topic_runs.py)

表示一次热点分析运行。关键字段：

- `id`
- `window_days`
- `article_count`
- `status`
- `model_name`
- `prompt_version`
- `raw_request`
- `raw_response`
- `error_message`

### HotTopic

[core/models/hot_topics.py](../../core/models/hot_topics.py)

表示某次运行产出的一个热点主题。关键字段：

- `id`
- `run_id`
- `topic_name`
- `summary`
- `signals_json`
- `article_count`
- `sort_order`

### HotTopicArticle

[core/models/hot_topic_articles.py](../../core/models/hot_topic_articles.py)

表示热点主题和文章之间的关联。

这套结构意味着：

- 热点不是直接挂在文章上的静态字段
- 它是某次分析运行的结果集
- 你可以追溯某次运行用了哪些文章、产出了哪些主题

## 8. 消息任务

### MessageTask

[core/models/message_task.py](../../core/models/message_task.py)

关键字段：

- `id`
- `name`
- `message_type`
- `message_template`
- `web_hook_url`
- `mps_id`
- `cron_exp`
- `status`

这里最容易误解的是 `mps_id`：

- 它不是单个公众号 ID
- 当前实现里常常是一个集合或 JSON 字符串语义

所以改消息任务时不要直接把它当普通外键。

## 9. API Key 与调用日志

### ApiKey

[core/models/api_key.py](../../core/models/api_key.py)

主要用于：

- 外部程序访问 API
- 区分用户密钥
- 控制启用状态和权限串

### ApiKeyLog

记录 API Key 的使用情况：

- 调了哪个 endpoint
- 用了什么 method
- 返回状态码
- 调用时间

如果你要做审计或限流，这是第一批会用到的数据。

## 10. 配置实体

### ConfigManagement

[core/models/config_management.py](../../core/models/config_management.py)

它表示“控制台里写入数据库的配置覆盖项”，不是全量配置源。

系统配置真实来源有多层：

- `config.yaml`
- `.env`
- 数据库覆盖
- 运行时环境变量

所以不要把它误当成唯一配置表。

## 11. 用户实体

### User

[core/models/user.py](../../core/models/user.py)

和本文档最相关的点只有两个：

- 登录认证依赖它
- API Key 归属依赖它

另外当前产品要求里，`username` 应视为稳定标识，展示名优先用 `nickname`。

## 12. 改模型时的检查清单

任何字段改动，都至少检查这几层：

1. 模型定义
2. API 返回
3. 前端展示
4. 导入导出
5. 定时任务是否依赖
6. 历史数据兼容性

最容易出问题的不是“加字段”，而是：

- 改字段语义
- 改字段类型
- 改默认值

因为这些会同时影响筛选、排序、导出和历史数据。
