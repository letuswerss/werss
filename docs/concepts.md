# 核心概念

下面把 WeRSS 里几个核心对象说透，读代码、看页面时，别把「公众号」「订阅」「Feed」「热点」「标签聚类」混为一谈。

## 1. 公众号 / mp

这是产品语义上的概念，表示一个微信公众号来源。

在实现里，它**没有**单独、稳定对外的「公众号」大表，职责多半落在 `Feed` 上。

所以读代码时，不妨先接受：

- 「公众号」
- 「订阅来源」
- 「Feed 记录」

说的是同一条主链、不同叫法。

## 2. Feed（订阅记录）

最核心的来源实体是 `Feed`。

位置：

- [core/models/feed.py](../core/models/feed.py)

它保存了：

- 公众号 ID
- 名称
- 封面图
- 简介
- 状态
- 同步时间
- 微信侧关联标识 `faker_id`

它既是：

- 采集入口
- 订阅管理页的数据源
- RSS 输出的上游实体

所以落地实现里，盯 `Feed` 比盯英文的 subscription 更靠谱。

## 3. subscription（订阅）

产品侧常说「订阅」，代码里却未必有一个叫 subscription 的稳态模型。页面上是：

- 订阅管理
- 添加订阅

真正落库、参与采集的，主要还是 `Feed`。

记一句就够：**界面说订阅，看代码先找 `Feed`。**

## 4. article（文章）

文章是整个系统的核心内容实体。

位置：

- [core/models/article.py](../core/models/article.py)
- [apis/article.py](../apis/article.py)
- [web_ui/src/views/ArticleListPage.tsx](../web_ui/src/views/ArticleListPage.tsx)

一篇文章通常包含：

- 标题
- 原文链接
- 摘要
- 正文
- 封面图
- 发布时间
- 所属公众号 ID

文章是这些能力的共同输入：

- 标签提取
- AI 过滤
- 热点发现
- RSS 输出
- 消息任务

## 5. tag（标签）

标签是文章的结构化关键词层。

位置：

- [core/models/tags.py](../core/models/tags.py)
- [apis/tags.py](../apis/tags.py)
- [web_ui/src/views/TagList.tsx](../web_ui/src/views/TagList.tsx)

一个标签可以：

- 来自 AI 提取
- 来自人工创建
- 关联多篇文章

标签是下游分析的基础信号，但它本身不是热点主题。

## 6. ArticleTag（文章-标签关联）

这是文章和标签之间的中间关系。

位置：

- [core/models/article_tags.py](../core/models/article_tags.py)

它表达的是：

- 一篇文章有多个标签
- 一个标签属于多篇文章

很多页面上的“标签文章数”或“文章标签列表”都依赖这张关系表统计。

## 7. AI 过滤状态

这是文章的另一层分析结果，不等于删除。

位置：

- [core/models/article_ai_filter.py](../core/models/article_ai_filter.py)

它的作用是：

- 判断一篇文章是保留、隐藏还是待定
- 让文章工作台可以默认隐藏低价值内容

所以“被过滤”不等于“被删掉”。

## 8. tag cluster（标签聚类）

标签聚类是“标签的聚合”，不是“文章的聚合”。

位置：

- [core/models/tag_clusters.py](../core/models/tag_clusters.py)
- [core/models/tag_cluster_members.py](../core/models/tag_cluster_members.py)
- [apis/tag_clusters.py](../apis/tag_clusters.py)

它表达的是：

- 多个语义相近的标签可以组成一个簇
- 一个簇有中心标签
- 聚类结果带版本号

标签聚类更适合解决：

- 标签碎片化
- 同义词 / 别名整理
- 语义归并

## 9. hot topic（热点主题）

热点主题是“文章的聚合”，不是标签的聚合。

位置：

- [core/models/hot_topics.py](../core/models/hot_topics.py)
- [core/models/hot_topic_runs.py](../core/models/hot_topic_runs.py)
- [core/models/hot_topic_articles.py](../core/models/hot_topic_articles.py)
- [apis/hot_topics.py](../apis/hot_topics.py)

它表达的是：

- 最近几天哪些文章其实在讲同一件事
- 每次分析都有运行记录
- 每个热点主题下面会挂一批文章

所以：

- `tag cluster` = 标签归堆
- `hot topic` = 文章归堆

这两个不要混。

## 10. message task（消息任务）

消息任务是系统的主动推送单元。

位置：

- [core/models/message_task.py](../core/models/message_task.py)
- [core/models/message_task_log.py](../core/models/message_task_log.py)
- [apis/message_task.py](../apis/message_task.py)

它至少包含这些要素：

- 任务名称
- 模板
- Webhook 地址
- cron 表达式
- 启用状态
- 关联公众号范围

消息任务的目标是：

- 按时间把文章整理后主动推送出去

## 11. RSS Feed

RSS 是文章的被动订阅输出层。

它不是独立内容源，而是基于 `Feed + Article` 动态生成的输出格式。

相关位置：

- [apis/rss.py](../apis/rss.py)

## 12. API Key

API Key 是程序化访问凭证。

位置：

- [core/models/api_key.py](../core/models/api_key.py)
- [apis/api_key.py](../apis/api_key.py)
- [web_ui/src/views/ApiKeyManagement.tsx](../web_ui/src/views/ApiKeyManagement.tsx)

它和登录态 JWT 不一样：

- JWT 是登录会话
- API Key 是长期给脚本或集成方使用的凭证

## 13. config override（配置覆盖）

这不是一个单独页面概念，但在系统里非常关键。

当前配置来源有多层：

- 配置文件
- `.env`
- 运行时环境变量
- 数据库中的配置覆盖

因此“设置页保存了配置”不等于“它就是系统唯一配置源”。

## 14. 概念关系图

```text
Feed（订阅来源 / 公众号）
  -> Article（文章）
     -> Tag（标签）
        -> Tag Cluster（标签聚类）
     -> AI Filter（文章过滤状态）
     -> Hot Topic（热点主题）

Feed + Article
  -> RSS 输出

Article + Feed
  -> Message Task（主动推送）

User
  -> API Key
```

## 15. 最重要的区分

如果只记住三件事，记住这三个区分就够了：

- `Feed` 是来源入口，不只是 RSS 概念
- `tag cluster` 是标签聚合，不是热点
- `hot topic` 是文章主题聚合，不是高频标签榜
