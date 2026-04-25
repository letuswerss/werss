# WeRSS 使用 uv 虚拟环境指南

## 📦 什么是 uv？

`uv` 是一个用 Rust 编写的极速 Python 包安装器和解析器，比传统的 `pip` 和 `venv` 快 10-100 倍。

## 🚀 快速开始

### 1. 安装 uv

```bash
# 使用官方安装脚本（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pipx
pipx install uv

# 或使用 pip（不推荐）
pip install uv
```

安装完成后，确保 `uv` 在 PATH 中：
```bash
# 如果使用官方安装脚本，uv 会被安装到 ~/.cargo/bin
export PATH="$HOME/.cargo/bin:$PATH"

# 验证安装
uv --version
```

### 2. 创建虚拟环境

```bash
cd /path/to/werss

# 使用 uv 创建虚拟环境（默认创建 .venv）
uv venv

# 或指定名称
uv venv venv

# 或指定 Python 版本
uv venv --python 3.11
```

### 3. 激活虚拟环境

```bash
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 4. 安装依赖

**方式一：使用 uv pip（推荐）**
```bash
# 激活虚拟环境后
uv pip install -r requirements.txt

# 使用国内镜像加速
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**方式二：使用 uv sync（如果使用 pyproject.toml）**
```bash
# uv sync 会根据 pyproject.toml 自动创建虚拟环境并安装依赖
uv sync
```

### 5. 启动服务

```bash
# 确保虚拟环境已激活
source .venv/bin/activate

# 设置环境变量
export DB=postgresql://user:pass@localhost:5432/werss_db
export WERSS_USERNAME=admin
export WERSS_PASSWORD=admin@123

# 初始化数据库（首次运行）
python main.py -init True

# 启动服务
python main.py -job True -init False
```

## 📝 完整示例

```bash
# 1. 进入项目目录
cd /path/to/werss

# 2. 创建虚拟环境
uv venv

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 安装依赖
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 配置环境变量
export DB=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/werss_db
export WERSS_USERNAME=admin
export WERSS_PASSWORD=admin@123
export DEBUG=True
export AUTO_RELOAD=True

# 6. 初始化数据库（首次运行）
python main.py -init True

# 7. 启动服务
python main.py -job True -init False
```

## 🔄 日常使用

### 激活虚拟环境

每次打开新的终端时，需要重新激活虚拟环境：

```bash
cd /path/to/werss
source .venv/bin/activate
```

### 更新依赖

```bash
# 激活虚拟环境后
uv pip install -r requirements.txt --upgrade
```

### 添加新依赖

```bash
# 方式一：手动编辑 requirements.txt，然后安装
uv pip install -r requirements.txt

# 方式二：使用 uv add（如果使用 pyproject.toml）
uv add package_name
```

### 退出虚拟环境

```bash
deactivate
```

## 🆚 uv vs 传统方式对比

| 操作 | 传统方式 | uv 方式 |
|------|---------|---------|
| 创建虚拟环境 | `python3 -m venv venv` | `uv venv` |
| 安装依赖 | `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| 速度 | 较慢 | 快 10-100 倍 |
| 激活方式 | `source venv/bin/activate` | `source .venv/bin/activate` |

## 💡 优势

1. **速度更快**：依赖安装和解析速度提升 10-100 倍
2. **自动管理**：自动处理 Python 版本和依赖冲突
3. **兼容性好**：完全兼容 pip 和 requirements.txt
4. **缓存机制**：自动缓存下载的包，加快后续安装

## ⚠️ 注意事项

1. **虚拟环境位置**：uv 默认创建 `.venv` 目录（而不是 `venv`）
2. **激活方式相同**：激活方式与传统 venv 完全相同
3. **依赖文件**：仍然使用 `requirements.txt`，无需修改
4. **Python 版本**：确保系统已安装 Python 3.11+

## 🔧 故障排除

### 问题1: uv 命令未找到

```bash
# 检查是否在 PATH 中
which uv

# 如果未找到，添加到 PATH
export PATH="$HOME/.cargo/bin:$PATH"

# 或重新安装
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 问题2: 虚拟环境激活失败

```bash
# 检查虚拟环境是否存在
ls -la .venv/

# 重新创建虚拟环境
rm -rf .venv
uv venv
source .venv/bin/activate
```

### 问题3: 依赖安装失败

```bash
# 使用国内镜像
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或清除缓存后重试
uv cache clean
uv pip install -r requirements.txt
```

## 📚 相关文档

- [uv 官方文档](https://docs.astral.sh/uv/)
- [WeRSS 快速开始指南](QUICK_START.md)
