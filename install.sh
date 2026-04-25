#!/bin/bash
plantform="$(uname -m)"
PLANT_PATH=${PLANT_PATH:-/app/data}
# 确保路径末尾没有斜杠
PLANT_PATH=${PLANT_PATH%/}
plant=$PLANT_PATH_$plantform

# 检测是否在 Docker 环境中，且系统已安装依赖
USE_SYSTEM_PYTHON=false
if [ -f /.dockerenv ] || [ -n "$DOCKER_CONTAINER" ]; then
    # 检查系统 Python 是否已安装 uvicorn（说明依赖已在构建时安装）
    if python3 -c "import uvicorn" 2>/dev/null; then
        echo "检测到 Docker 环境且系统已安装依赖，使用系统 Python"
        USE_SYSTEM_PYTHON=true
    fi
fi

# 如果不需要使用系统 Python，则创建虚拟环境
if [ "$USE_SYSTEM_PYTHON" = false ]; then
python3 -m venv $plant
source $plant/bin/activate
echo "使用虚拟环境: $plant"
else
    echo "使用系统 Python（Docker 环境）"
fi


# 检查函数：检查包是否已安装
check_package() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "$1 已安装"
        return 0
    elif dpkg -l "$1" 2>/dev/null | grep -q "^ii"; then
        echo "$1 已安装"
        return 0
    else
        echo "$1 未安装"
        return 1
    fi
}
# 检查所有需要的包
packages=("wget" "git" "build-essential" "zlib1g-dev" 
          "libgdbm-dev" "libnss3-dev" "libssl-dev" "libreadline-dev" 
          "libffi-dev" "libsqlite3-dev" "procps" )



if [ "$EXPORT_PDF" = "True" ]; then
    echo "添加libreoffice依赖包..."
    packages+=("fonts-noto-cjk" "libreoffice")
fi

echo "检查依赖包安装状态..."
for package in "${packages[@]}"; do
    if ! check_package "$package"; then
        missing_packages+=("$package")
    fi
done
echo "${missing_packages[*]}"
if [ ${#missing_packages[@]} -eq 0 ]; then
    echo "所有依赖都已安装，无需重复安装。"
else
    echo "需要安装的包: ${missing_packages[*]}"
    echo "开始安装..."
    apt update && apt install -y ${missing_packages[*]} --no-install-recommends\
        && rm -rf /var/lib/apt/lists/*
    if [ $? -eq 0 ]; then
        echo "安装完成！"
    else
        echo "安装失败！"
        exit 1
    fi
fi

ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-$PLANT_PATH/driver/_$plantform}
BROWSER_TYPE=${BROWSER_TYPE:-webkit}
echo "export PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH}
export TZ=Asia/Shanghai
export BROWSER_TYPE=${BROWSER_TYPE}">/app/environment.sh
echo "环境变量已设置"
chmod +x /app/environment.sh
cat /app/environment.sh
source /app/environment.sh
if [ "$USE_SYSTEM_PYTHON" = false ]; then
echo "source /app/environment.sh
source $plant/bin/activate">/etc/profile
else
    echo "source /app/environment.sh">/etc/profile
fi
# 安装 uv（如果未安装）
if ! command -v uv >/dev/null 2>&1; then
    echo "安装 uv 包管理器..."
    pip3 install uv --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

# 检查requirements.txt更新
if [ -f "requirements.txt" ]; then
    # 如果使用系统 Python 且依赖已安装，跳过安装步骤
    if [ "$USE_SYSTEM_PYTHON" = true ]; then
        echo "使用系统 Python，依赖已在构建时安装，跳过安装步骤"
    else
    CURRENT_MD5=$(md5sum requirements.txt | cut -d' ' -f1)
    OLD_MD5_FILE="$PLANT_PATH/requirements.txt.md5"
    
    if [ -f "$OLD_MD5_FILE" ] && [ "$CURRENT_MD5" = "$(cat $OLD_MD5_FILE)" ]; then
        echo "requirements.txt未更新，跳过安装"
    else
        echo "使用 uv 安装requirements.txt依赖..."
        # 优先使用 uv，如果失败则回退到 pip
        uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple || \
        pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
        echo $CURRENT_MD5 > $OLD_MD5_FILE
        fi
    fi
fi 

INSTALL=${INSTALL:-False}
# 根据环境变量决定是否安装浏览器
if [ "$INSTALL" = True ]; then
    echo "INSTALL环境变量为$INSTALL，开始安装playwright浏览器..."
    
    # 检测系统架构；国内镜像常滞后，404 时回退官方 CDN（与 Dockerfile.cn 一致）
    ARCH=$(uname -m)
    export PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=300000
    if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
        echo "检测到 ARM 架构 ($ARCH)，使用官方 Playwright 下载源"
        export PLAYWRIGHT_DOWNLOAD_HOST=https://playwright.azureedge.net
    else
        echo "检测到 x86_64/AMD64，先尝试 npmmirror"
        export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
    fi
    if ! playwright install $BROWSER_TYPE --with-deps; then
        echo "主下载源失败（npmmirror 未同步新版浏览器包时会出现），改用 playwright.azureedge.net 重试..."
        export PLAYWRIGHT_DOWNLOAD_HOST=https://playwright.azureedge.net
        playwright install $BROWSER_TYPE --with-deps || echo "Playwright 浏览器安装仍失败，采集功能可能不可用"
    fi
else
    echo "INSTALL环境变量为$INSTALL，跳过playwright浏览器安装"
fi