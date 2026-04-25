# 文章列表查询 API 说明

基础路径前缀以部署为准，默认为 **`/api/v1/wx`**。

## 认证

以下接口需要登录后的 **JWT**（`Authorization: Bearer <token>`）或 **API Key**：

- 请求头：`X-API-Key: werss_xxxx`
- 或：`Authorization: Bearer werss_xxxx`（当值中不含 `.` 时按 API Key 处理，与 JWT 区分）

API Key 在 Web 端 **「API Key 管理」** 页面创建。

## 获取文章列表

`GET` 或 `POST` **`/api/v1/wx/articles`**

### 分页与排序

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `offset` | int | 0 | 偏移量，≥0 |
| `limit` | int | 5 | 每页条数，1～100 |

列表按 **`publish_time` 降序**（新文章在前）。

### 基础筛选

| 参数 | 类型 | 说明 |
|------|------|------|
| `status` | string | 文章状态；不传则排除已删除 |
| `search` | string | 标题关键词，空格/`|`/`-` 拆成多词，**OR** 匹配 |
| `mp_id` | string | 仅某公众号 |
| `has_content` | bool | `true` 时只查含 `content` 字段的完整记录 |

### 发布时间（`publish_time` 存库为毫秒时间戳）

| 参数 | 类型 | 说明 |
|------|------|------|
| `publish_from` | int | 起始时间（含）。若数值 **&lt; 10¹²** 视为**秒**，否则视为**毫秒** |
| `publish_to` | int | 结束时间（含）。规则同上 |

可与下面「日期」参数同时使用：取**更严**的区间（下界取较大、上界取较小）。

### 按日历日筛选（UTC）

| 参数 | 类型 | 说明 |
|------|------|------|
| `publish_date_from` | string | `YYYY-MM-DD`，该日 00:00:00 UTC（含） |
| `publish_date_to` | string | `YYYY-MM-DD`，该日 23:59:59.999 UTC（含） |

### 标签筛选

| 参数 | 类型 | 说明 |
|------|------|------|
| `tag_id` | string | 单个标签 ID |
| `tag_ids` | string | 多个标签 ID，**逗号分隔** |
| `tag_match` | string | `any`（默认）：命中**任一**标签即可；`all`：必须同时包含**全部**所列标签 |

标签 ID 与 **`GET /api/v1/wx/tags`** 返回的 `id` 一致。

### 响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [ /* 文章对象，含 mp_name、mp_cover、tags、tag_names */ ],
    "total": 123
  }
}
```

### 示例

```bash
# JWT
curl -s -H "Authorization: Bearer YOUR_JWT" \
  "http://localhost:8001/api/v1/wx/articles?limit=20&offset=0&mp_id=MP_WXS_xxx&search=AI"

# API Key + 日期 + 标签（任一命中）
curl -s -H "X-API-Key: werss_your_key" \
  "http://localhost:8001/api/v1/wx/articles?limit=10&publish_date_from=2026-03-01&publish_date_to=2026-03-20&tag_ids=id1,id2&tag_match=any"
```

### 缓存

相同查询条件结果可能缓存约 **5 分钟**（内存缓存）；筛选参数均参与缓存键，更新后稍候即可看到最新数据或重启服务。

---

更多全局说明见 [README.md](../README.md) 中的「API 文档」与 Swagger：`/api/docs`。
