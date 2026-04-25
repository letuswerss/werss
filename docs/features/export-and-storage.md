# 导出与存储

## 1. 功能目标

导出与存储模块负责将 WeRSS 中的数据（公众号、标签）导出为标准格式文件，并管理文章中图片的存储策略。

## 2. 适用场景

- 将公众号列表导出为 CSV 或 OPML，供备份或迁移
- 将标签列表导出为 CSV，供批量编辑后重新导入
- 文章图片从微信服务器转存到 MinIO，避免图片失效
- 公众号头像统一上传到 MinIO，保证展示一致性

## 3. 核心对象

| 对象 | 说明 |
|------|------|
| `Feed` | 公众号订阅，`feeds` 表，一条记录对应一个公众号 |
| `Tags` | 标签，`tags` 表 |
| `Article` | 文章，`articles` 表 |
| MinIO Bucket | 对象存储空间，存储图片和头像 |

## 4. 数据流 / 工作流程

### 4.1 公众号导出

```
用户请求 /export/mps/export
    │
    ├── 查询 Feed 表，按关键词筛选
    │
    ├── 构建 CSV 数据（id, 公众号名称, 封面图, 简介, 状态, 创建时间, faker_id）
    │
    ├── 创建临时 CSV 文件（temp_mp_export.csv）
    │
    └── 返回 FileResponse，浏览器下载完成后自动删除临时文件
```

**支持的导出格式：**

- **CSV**：适合 Excel 编辑和数据分析
- **OPML**：标准的 RSS 订阅列表格式，可导入其他 RSS 阅读器

```
GET /export/mps/export        → CSV 文件下载
GET /export/mps/opml          → OPML 文件下载
```

### 4.2 标签导出 / 导入

```
导出：GET /export/tags
    ├── 查询 Tags 表
    ├── 生成 CSV（id, 标签名称, 封面图, 描述, 状态, 创建时间, mps_id）
    └── 返回下载

导入：POST /export/tags/import
    ├── 验证 CSV 必要列（标签名称、状态、mps_id）
    ├── 遍历每行：
    │   ├── 根据 id 查找是否已存在
    │   ├── 存在则更新，不存在则创建
    │   └── 跳过空名称的行
    └── 返回统计（导入数、更新数、跳过数）
```

### 4.3 图片转存 MinIO

当文章从微信抓取后，系统可以将正文中引用的图片转存到 MinIO：

```
文章抓取完成
    │
    ├── 检查 minio.enabled 和 minio.store_article_images 配置
    │
    ├── 对每张图片：
    │   ├── 下载原始图片到内存
    │   ├── 用 URL 的 MD5 哈希作为文件名（避免重复）
    │   ├── 上传到 MinIO bucket: articles/{article_id}/{filename}
    │   └── 替换文章内容中的图片 URL 为 MinIO 地址
    │
    └── 头像处理类似：avatars/{mp_id}/{filename}
```

**存储路径规则：**

| 资源类型 | MinIO 中的路径 |
|----------|----------------|
| 文章图片 | `articles/{article_id}/{md5hash}.{ext}` |
| 公众号头像 | `avatars/{clean_mp_id}/{md5hash}.{ext}` |

**MinIO 访问方式：**

- **公开 Bucket**：`{public_url}/{bucket}/{object_name}` 或 `{endpoint}/{bucket}/{object_name}`
- **私有 Bucket**（`use_presigned_url=True`）：生成 7 天有效的 presigned URL

## 5. 主要能力

### 5.1 公众号导入 / 导出

| API | 方法 | 说明 |
|-----|------|------|
| `/export/mps/export` | GET | 导出公众号 CSV |
| `/export/mps/import` | POST | 导入公众号 CSV（支持增量更新） |
| `/export/mps/opml` | GET | 导出公众号 OPML |

### 5.2 标签导入 / 导出

| API | 方法 | 说明 |
|-----|------|------|
| `/export/tags` | GET | 导出标签 CSV |
| `/export/tags/import` | POST | 导入标签 CSV（支持增量更新） |

### 5.3 图片转存

| 函数 | 说明 |
|------|------|
| `MinIOClient.upload_image()` | 下载并上传文章图片到 MinIO |
| `MinIOClient.upload_avatar()` | 下载并上传公众号头像到 MinIO |
| `should_mirror_article_images()` | 业务开关，判断是否启用转存 |

## 6. 关键配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `minio.enabled` | 是否启用 MinIO | `False` |
| `minio.endpoint` | MinIO 服务地址（如 `minio.example.com:9000`） | - |
| `minio.access_key` | Access Key | - |
| `minio.secret_key` | Secret Key | - |
| `minio.bucket` | Bucket 名称 | `articles` |
| `minio.public_url` | 公开访问的基础 URL | - |
| `minio.secure` | 是否使用 HTTPS | `False` |
| `minio.use_presigned_url` | 是否使用 presigned URL（私有 bucket） | `False` |
| `minio.store_article_images` | 是否转存文章图片，建议仅在有授权或私有归档需求时开启 | `False` |

## 7. 关联页面与 API

| 资源 | 页面 | API |
|------|------|-----|
| 公众号导出 | 公众号列表页右上角"导出"按钮 | `GET /export/mps/export` |
| 公众号导入 | 公众号列表页右上角"导入"按钮 | `POST /export/mps/import` |
| 标签导出 | 标签列表页右上角"导出标签"按钮 | `GET /export/tags` |
| 标签导入 | 标签列表页右上角"导入标签"按钮 | `POST /export/tags/import` |
| OPML 导出 | （无独立页面，通过 URL 访问） | `GET /export/mps/opml` |

## 8. 常见问题 / 限制

- **导入 CSV 格式错误**：缺少必要列（`标签名称`、`状态`、`mps_id`）时返回 400 错误
- **导入标签名称为空**：自动跳过该行，不影响其他行
- **MinIO 未安装**：`pip install minio`，未安装时图片转存功能不可用，控制台会输出警告
- **MinIO 配置不完整**：即使 `minio.enabled=True`，配置不完整时客户端不会初始化
- **图片转存失败**：网络问题或原图失效时返回 `None`，不影响文章抓取流程
- **合规边界**：不建议默认转存第三方图片或将导出文件用于公开传播
- **临时文件清理**：导出文件在响应发送后由 `BackgroundTask` 自动删除

## 9. 相关文件

```
apis/export.py                  # 导入/导出 API 路由
core/storage/minio_client.py    # MinIO 客户端
core/content_format.py          # 内容格式化（Markdown/PDF 相关）
core/rss.py                     # RSS 生成（含 OPML）
web_ui/src/views/TagList.tsx    # 标签列表（含导入/导出按钮）
web_ui/src/views/TagForm.tsx    # 标签编辑表单
```
