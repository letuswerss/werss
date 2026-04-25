# 标签聚类上线检查清单

本文档用于在启用或重新部署标签聚类能力前做快速核对，避免“页面能打开，但聚类数据没准备好”的情况。

## 1. 上线前检查

- 确认标签聚类相关表已经创建完成：
  - `tag_profiles`
  - `tag_embeddings`
  - `tag_similarities`
  - `tag_clusters`
  - `tag_cluster_members`
- 确认已经配置至少一种 embedding 提供方：
  - `TAG_CLUSTER_EMBEDDING_PROVIDER=bigmodel` 并配置 `BIGMODEL_API_KEY`
  - 或 `TAG_CLUSTER_EMBEDDING_PROVIDER=doubao` 并配置 `DOUBAO_API_KEY`
- 确认聚类功能开关已启用：
  - `TAG_CLUSTER_ENABLED=true`

## 2. 本地验证

- 先做 Python 语法检查：

```bash
python3 -m py_compile \
  apis/tag_clusters.py \
  core/tag_cluster.py \
  core/embedding/*.py \
  core/models/tag_*.py \
  scripts/build_tag_clusters.py
```

- 再做前端构建检查：

```bash
cd web_ui
npm run build
```

- 最后执行一次离线重建：

```bash
python3 scripts/build_tag_clusters.py
```

## 3. 部署后验证

- 打开 `/tag-clusters` 页面，确认聚类列表能正常加载
- 进入任意一个聚类详情页
- 确认以下区域都有数据：
  - 聚类摘要
  - 成员标签
  - 相似标签
  - 合并建议
- 点击“导出 JSON”，确认导出的内容包含：
  - 聚类元数据
  - 成员列表
  - 合并建议

## 4. 常见异常

### 页面能打开，但列表为空

优先检查：

- 聚类重建是否真的执行过
- embedding 提供方是否配置正确
- 标签表中是否已有足够标签数据

### 重建报错提示未配置 API Key

说明 embedding 提供方已经启用，但对应密钥未配置完整。先补 `.env` 或运行环境变量，再重建。

### 聚类详情能开，但没有相似标签或合并建议

优先检查：

- 标签相似度表是否生成
- 当前标签数据是否过少
- 阈值是否过高
