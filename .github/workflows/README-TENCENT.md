# 腾讯云容器镜像服务配置指南

## 前置准备

1. **在腾讯云控制台创建容器镜像服务实例**
   - 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
   - 进入「容器镜像服务」或「容器服务」
   - 创建命名空间（Namespace）
   - 创建镜像仓库

2. **获取访问凭证**
   - 在腾讯云控制台的「访问管理」中创建 API 密钥
   - 或者使用镜像仓库的访问凭证（用户名/密码）

## GitHub Secrets 配置

在你的 GitHub 仓库中，进入 `Settings` → `Secrets and variables` → `Actions`，添加以下 secrets：

### 必需配置

- `TENCENT_REGISTRY_USERNAME`: 腾讯云容器镜像服务的用户名
- `TENCENT_REGISTRY_PASSWORD`: 腾讯云容器镜像服务的密码或访问令牌

### 可选配置

- `TENCENT_REGISTRY`: 镜像仓库地址（默认：`ccr.ccs.tencentyun.com`）
  - 旧版：`ccr.ccs.tencentyun.com`
  - 新版：`mirror.ccs.tencentyun.com`
- `TENCENT_IMAGE_NAMESPACE`: 镜像命名空间（默认：`default`）

## 工作流说明

### docker-tencent.yaml

专门用于推送到腾讯云容器镜像服务的工作流：
- 触发条件：推送到 `main` 分支，或手动触发
- 构建多架构镜像：`linux/amd64` 和 `linux/arm64`
- 使用 `Dockerfile.cn`（国内镜像源版本，构建更快）
- 自动生成多个标签：`latest`、分支名、SHA 等

### docker-publish.yaml（已更新）

已更新为同时推送到 GitHub Container Registry 和腾讯云：
- 如果配置了腾讯云 secrets，会自动推送到两个仓库
- 如果没有配置腾讯云 secrets，只推送到 GitHub Container Registry

## 使用方法

### 方法一：使用独立工作流（推荐）

1. 配置 GitHub Secrets（见上方）
2. 推送到 `main` 分支，工作流会自动触发
3. 或手动触发：`Actions` → `Build and Push to Tencent Cloud Container Registry` → `Run workflow`

### 方法二：使用更新后的 docker-publish.yaml

1. 配置 GitHub Secrets（见上方）
2. 推送到 `main` 分支，工作流会自动同时推送到 GitHub 和腾讯云

## 拉取镜像

构建完成后，可以在腾讯云服务器上拉取镜像：

```bash
# 登录腾讯云容器镜像服务
docker login ccr.ccs.tencentyun.com -u <用户名> -p <密码>

# 拉取镜像
docker pull ccr.ccs.tencentyun.com/<命名空间>/werss:latest

# 运行容器
docker run -d -p 8001:8001 ccr.ccs.tencentyun.com/<命名空间>/werss:latest
```

## 注意事项

1. **镜像命名空间**：确保在腾讯云控制台已创建对应的命名空间
2. **访问权限**：确保 API 密钥或访问凭证有推送镜像的权限
3. **网络**：GitHub Actions 运行在海外，推送到腾讯云可能需要一些时间
4. **费用**：腾讯云容器镜像服务可能有存储和流量费用，请查看腾讯云定价

## 故障排查

### 认证失败

- 检查 `TENCENT_REGISTRY_USERNAME` 和 `TENCENT_REGISTRY_PASSWORD` 是否正确
- 确认访问凭证是否过期
- 检查是否有推送权限

### 推送失败

- 检查命名空间是否存在
- 确认镜像仓库是否已创建
- 查看 GitHub Actions 日志获取详细错误信息

### 构建缓慢

- 工作流已配置缓存（`cache-from` 和 `cache-to`），第二次构建会更快
- 使用 `Dockerfile.cn` 可以加速构建（使用国内镜像源）

