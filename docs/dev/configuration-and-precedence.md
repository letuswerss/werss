# 配置与优先级

## 1. 文档目的

本文档面向部署工程师和开发者，解释 WeRSS 的配置来源、加载顺序和优先级规则。帮助解决"改了配置不生效""环境变量和数据库哪个优先"等问题。

## 2. 配置来源

WeRSS 配置有四个来源，按优先级从低到高：

| 来源 | 说明 |
|---|---|
| `config.example.yaml` | 默认配置示例文件，不参与实际加载 |
| `config.yaml` | 用户配置文件，支持 `${VAR:-default}` 环境变量插值 |
| `.env` | 开发环境环境变量文件（仅开发环境加载） |
| 数据库 `config_management` 表 | Web UI 控制台写入的配置 |
| 环境变量 | 运行时环境变量，直接覆盖 yaml 值 |

## 3. 配置加载流程

`core/config.py` 的 `Config.get()` 方法实现三层解析：

```
1. 解析 config.yaml（支持 ${VAR:-default} 插值）
2. 解析环境变量覆盖（已展开的值优先于 yaml 中未展开的）
3. 解析数据库覆盖（WERSS_ENV_OVERRIDES_DB 控制优先级）
```

### 3.1 yaml + 环境变量插值

`config.yaml` 中的 `${VAR:-default}` 语法：
- `VAR`：环境变量名
- `default`：如果环境变量未设置，使用此默认值

**示例**：
```yaml
db: ${DB:-sqlite:///data/db.db}
```
如果环境变量 `DB` 未设置，使用 `sqlite:///data/db.db`；否则使用 `DB` 的值。

### 3.2 数据库覆盖层

Web UI 的"系统设置"页面保存配置时，写入 `config_management` 表。

数据库覆盖的优先级由 `WERSS_ENV_OVERRIDES_DB` 环境变量控制：

| `WERSS_ENV_OVERRIDES_DB` | 行为 |
|---|---|
| 未设置 / `false`（默认） | `config_management` 表优先。只要表中有该键，返回表中的值；仅当表中无该键时回退到 yaml/环境变量。 |
| `true` | yaml + 环境变量优先。仅当 yaml/环境变量中该键未设置或为空字符串时，才回退到 `config_management` 表。 |

**`WERSS_ENV_OVERRIDES_DB` 的典型场景**：
- 共享部署（多实例共用数据库）：设为 `true`，各实例用环境变量覆盖自己想覆盖的键
- 单实例部署：默认行为即可，控制台保存的配置直接生效

### 3.3 特殊键 `db`

数据库连接串 `db` 永远不走 `config_management` 表覆盖，只从 `config.yaml` + 环境变量读取。

## 4. 配置优先级总结

以 `minio.store_article_images` 为例，假设在 Web UI 中保存为 `false`：

| 环境变量 `MINIO_STORE_ARTICLE_IMAGES` | `WERSS_ENV_OVERRIDES_DB` | 实际值 |
|---|---|---|
| 未设置 | `false`（默认） | `false`（来自数据库） |
| `true` | `false`（默认） | `true`（环境变量覆盖 yaml，但数据库优先） |
| `true` | `true` | `true`（环境变量 > yaml > 数据库，且非空） |
| 未设置 | `true` | 数据库回退值（如果有） |

**简化原则**：
- `WERSS_ENV_OVERRIDES_DB=false`（默认）：数据库 > yaml > 环境变量
- `WERSS_ENV_OVERRIDES_DB=true`：环境变量/yaml > 数据库（仅空时回退）

## 5. 关键配置项

### 5.1 数据库连接

```yaml
db: ${DB:-sqlite:///data/db.db}
```

支持：
- SQLite：`sqlite:///data/db.db`
- MySQL：`mysql+pymysql://user:password@host:3306/werss?charset=utf8mb4`
- PostgreSQL：`postgresql://user:password@host:5432/werss`

**注意**：连接串格式必须正确，MySQL 用 `mysql+pymysql://`，PostgreSQL 用 `postgresql://`。

### 5.2 定时任务开关

```yaml
server:
  enable_job: ${ENABLE_JOB:-True}
```

与启动参数 `-job True` 共同决定是否启动 APScheduler 调度器。两者都为真才启动。

### 5.3 文章清理

```yaml
article:
  true_delete: ${ARTICLE.TRUE_DELETE:-True}  # true=物理删除，false=逻辑删除（标记 status）
  retention:
    enabled: ${ARTICLE_RETENTION_ENABLED:-false}
    days: ${ARTICLE_RETENTION_DAYS:-7}
    basis: ${ARTICLE_RETENTION_BASIS:-created_at}  # created_at 或 publish_time
    cron: ${ARTICLE_RETENTION_CRON:-0 4 * * *}  # 默认每天 4:00
```

### 5.4 MinIO 对象存储

```yaml
minio:
  enabled: ${MINIO_ENABLED:-False}
  store_article_images: ${MINIO_STORE_ARTICLE_IMAGES:-False}
  endpoint: ${MINIO_ENDPOINT:-localhost:9000}
  access_key: ${MINIO_ACCESS_KEY:-minioadmin}
  secret_key: ${MINIO_SECRET_KEY:-minioadmin}
  bucket: ${MINIO_BUCKET:-articles}
  secure: ${MINIO_SECURE:-False}
  public_url: ${MINIO_PUBLIC_URL:-http://localhost:9000}
```

### 5.5 RSS

```yaml
rss:
  base_url: ${RSS_BASE_URL:-}  # RSS 域名，填写真实域名后 RSS 链接才正确
  local: ${RSS_LOCAL:-False}  # True=本地代理链接，False=直接输出微信原文链接
  full_context: ${RSS_FULL_CONTEXT:-False}  # True=输出全文，False=仅输出摘要
  add_cover: ${RSS_ADD_COVER:-False}  # True=添加封面图片 enclosure
  cdata: ${RSS_CDATA:-False}  # True=内容用 CDATA 包裹
  page_size: ${RSS_PAGE_SIZE:-10}  # 每页文章数量
```

### 5.6 标签提取

```yaml
article_tag:
  auto_extract: ${ARTICLE_TAG_AUTO_EXTRACT:-False}
  max_tags: ${ARTICLE_TAG_MAX_TAGS:-5}

openai:
  api_key: ${OPENAI_API_KEY:-}
  base_url: ${OPENAI_BASE_URL:-https://api.openai.com/v1}
  model: ${OPENAI_MODEL:-gpt-4o}
```

### 5.7 采集配置

```yaml
gather:
  content: ${GATHER.CONTENT:-False}  # 是否采集正文
  model: ${GATHER.MODEL:-app}  # app/api/web
  browser_type: ${BROWSER_TYPE:-firefox}
  content_auto_check: ${GATHER.CONTENT_AUTO_CHECK:-False}
```

## 6. .env 文件（仅开发环境）

开发环境下，`core/config.py` 会在初始化前尝试加载项目根目录的 `.env` 文件：

```python
# 仅在非 Docker 环境中加载
if not is_docker:
    load_dotenv('.env', override=False)
```

Docker 部署时不加载 `.env`，环境变量由 `docker-compose.yml` 注入。

## 7. 常见问题

### 7.1 改了 .env 配置文件不生效

检查：
1. 是否在 Docker 环境（Docker 环境不加载 `.env`）
2. 是否设置了 `WERSS_ENV_OVERRIDES_DB=true`（此时 yaml/环境变量优先于数据库）
3. `config_management` 表中是否存在该键（数据库值可能覆盖了环境变量）

### 7.2 Web UI 保存的配置不生效

原因：`WERSS_ENV_OVERRIDES_DB=true` 时，环境变量和 yaml 优先于数据库。

解决：在 `.env` 或 `config.yaml` 中明确设置该配置项，或将 `WERSS_ENV_OVERRIDES_DB` 设为 `false`。

### 7.3 文章清理不执行

需要同时满足：
- `article.retention.enabled=true` 或环境变量 `ARTICLE_RETENTION_ENABLED=true`
- `server.enable_job=true`（`ENABLE_JOB=True`）
- 进程启动时带 `-job True` 参数

### 7.4 MinIO 图片转存不生效

检查：
1. `minio.enabled=true`
2. MinIO 服务可访问（endpoint 正确，防火墙开放 9000 端口）
3. `minio.store_article_images=true`（或在 Web UI 设置中开启）
4. 存储桶已创建且 access_key/secret_key 正确

## 8. 相关文件

- `core/config.py` — 配置加载器，`cfg.get()` 实现
- `core/config_overrides.py` — 数据库覆盖层，`WERSS_ENV_OVERRIDES_DB` 逻辑
- `config.example.yaml` — 配置示例
- `docs/DEPLOYMENT.md` — 部署文档（包含 docker-compose 环境变量说明）
