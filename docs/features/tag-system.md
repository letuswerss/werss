# 标签系统

## 1. 功能目标

为文章打标签，实现文章分类、筛选和聚合。标签是热点发现、标签聚类的前置数据。

## 2. 适用场景

- 用户手动管理标签，对文章进行分类
- AI 自动从文章内容中提取标签
- 按标签筛选文章列表
- 标签聚类前需要先有标签数据

## 3. 核心对象

| 对象 | 说明 |
|------|------|
| `Tags` | 标签实体，`tags` 表 |
| `ArticleTag` | 文章-标签关联，`article_tags` 表 |
| `is_custom` | 区分手动标签与 AI 标签（`is_custom=True` 为手动） |

## 4. 数据流 / 工作流程

```
文章 → AI 提取标签 → Tags 表
      ↓
手动创建标签 → Tags 表
      ↓
标签关联文章 → ArticleTag 表
      ↓
标签筛选 / 标签聚类 / 热点发现
```

### 4.1 AI 提取标签

- 触发：`core/tag_extractor.py` 的 `TagExtractor.extract_with_ai()`
- 调用 OpenAI 兼容 API（配置项 `openai.api_key` / `openai.base_url` / `openai.model`）
- Prompt 模板中优先匹配用户自定义标签（`is_custom=True`）
- 配置项：`article_tag.max_tags`（默认 5）、`article_tag.ai_prompt`（自定义 prompt）

### 4.2 手工标签与 AI 标签的关系

- **手工标签：** `Tags.is_custom = True`，用户在 `/tags` 页面手动创建
- **AI 标签：** 系统通过 LLM 自动提取，不标记 `is_custom`
- 两者共存于同一张 `tags` 表，通过 `is_custom` 字段区分
- 手工标签会被缓存到 TagExtractor 中，用于 AI 提取时的优先匹配

## 5. 主要能力

### 5.1 标签管理（CRUD）

- API：`POST /api/v1/wx/tags`（创建）、`GET /api/v1/wx/tags`（列表）
- API：`PUT /api/v1/wx/tags/{tag_id}`（更新）、`DELETE /api/v1/wx/tags/{tag_id}`（删除）
- 批量删除：`DELETE /api/v1/wx/tags?tag_ids=id1,id2`

### 5.2 文章标签关联

- API：`POST /api/v1/wx/article-tag`（关联标签到文章）
- API：`GET /api/v1/wx/article-tag?article_id=xxx`（获取文章的所有标签）
- API：`DELETE /api/v1/wx/article-tag/{tag_id}?article_id=xxx`（删除关联）

### 5.3 标签筛选

- 文章列表 API 支持 `tag_id` / `tag_ids` 筛选
- 筛选标签通过 `is_filter` 字段区分（与普通标签存在同一张表）

### 5.4 标签聚类（见 `docs/features/tag-clusters.md`）

- 标签 → 标签聚类，是独立功能，不在本节讨论范围

## 6. 关键配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `openai.api_key` | AI API Key | - |
| `openai.base_url` | API Base URL | https://api.openai.com/v1 |
| `openai.model` | 模型名称 | gpt-4o |
| `article_tag.max_tags` | 每次提取标签数 | 5 |
| `article_tag.ai_prompt` | 自定义 prompt 模板 | 内置默认模板 |

## 7. 关联页面与 API

- **Web UI：** `/tags`（标签列表）、文章详情页（标签展示）
- **API：**
  - `GET /api/v1/wx/tags` - 标签列表（分页，含近 3 天文章数）
  - `POST /api/v1/wx/tags` - 创建标签
  - `PUT /api/v1/wx/tags/{tag_id}` - 更新标签
  - `DELETE /api/v1/wx/tags/{tag_id}` - 删除标签
  - `POST /api/v1/wx/tags/test/extract` - 测试 AI 提取
  - `POST /api/v1/wx/article-tag` - 为文章添加标签
  - `GET /api/v1/wx/article-tag` - 获取文章的所有标签

## 8. 常见问题 / 限制

- **AI 提取失败：** API Key 未配置或网络问题会导致提取失败，返回空列表
- **标签同名冲突：** 标签名称相同时系统不会去重，需业务层处理
- **删除标签：** 删除标签时自动清除 ArticleTag 关联记录

## 9. 相关文件

```
core/tag_extractor.py          # 标签提取逻辑
core/models/tags.py           # Tags 模型
core/models/article_tags.py  # ArticleTag 模型
apis/tags.py                 # 标签管理 API
apis/article_tag.py          # 文章-标签关联 API
web_ui/src/views/TagList.tsx  # 标签列表页面
```
