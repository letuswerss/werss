# WeRSS 远程 MCP 接入

WeRSS 现在暴露了一个远程 MCP 入口：

- `GET /mcp`
- `POST /mcp`

这是一个基于 Streamable HTTP 的 MCP endpoint。当前实现优先支持工具调用；如果客户端只发 `POST`，也可以正常工作。

## 环境变量

建议配置以下变量：

- `WERSS_MCP_TOKEN`
  - MCP 访问令牌
  - 如果设置了，所有请求都必须带 `Authorization: Bearer <token>` 或 `X-MCP-Token: <token>`
- `MCP_ALLOWED_ORIGINS`
  - 允许的 Origin 列表，逗号分隔
  - 例如：`https://your-domain.com,https://app.your-domain.com`

## 客户端配置

客户端可直接指向：

```text
https://your-domain.com/mcp
```

请求头：

```text
Authorization: Bearer YOUR_MCP_TOKEN
```

## 已暴露工具

- `articles.list`
- `articles.get`
- `articles.toggle_status`
- `articles.ai_filter`
- `articles.ai_filter_restore`
- `tags.list`
- `tags.get`
- `tags.toggle_status`
- `tag_clusters.list`
- `tag_clusters.get`
- `tag_clusters.visualization`
- `tag_clusters.network`

## 说明

- `articles.ai_filter` 会执行 AI 过滤并写入数据库
- `articles.ai_filter_restore` 会恢复 AI 过滤结果并把文章重新启用
- `tags.toggle_status` 会切换标签启用/禁用状态
- `tag_clusters.visualization` 和 `tag_clusters.network` 直接返回可视化数据

