#!/bin/bash

# 检查是否以 root 用户运行
if [[ "$(uname -s)" != "MINGW"* && "$(uname -s)" != "CYGWIN"* ]]; then
    if [ "$EUID" -ne 0 ]; then
        echo "请使用 root 用户或使用 sudo 运行此脚本"
        exit 1
    fi
fi

# 配置文件路径
DEFAULT_CONFIG="obs.conf"
CONFIG_FILE="$DEFAULT_CONFIG"

# 检查配置文件是否存在并可读
if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 配置文件 $CONFIG_FILE 不存在" >&2
    echo "请确保配置文件存在并包含以下必需参数:" >&2
    echo "OBS_ACCESS_KEY: 华为云OBS访问密钥" >&2
    echo "OBS_SECRET_KEY: 华为云OBS密钥" >&2
    echo "OBS_BUCKET_NAME: OBS存储桶名称" >&2
    echo "OBS_ENDPOINT: OBS服务端点" >&2
    echo "LOCAL_MOUNT_POINT: 本地挂载点路径" >&2
    if [[ "$(uname -s)" == "MINGW"* || "$(uname -s)" == "CYGWIN"* ]]; then
        echo "Windows用户提示:" >&2
        echo "1. 请确保配置文件与脚本在同一目录或提供完整路径" >&2
        echo "2. 配置文件扩展名应为.conf" >&2
        echo "3. 示例配置文件内容:" >&2
        echo "   OBS_ACCESS_KEY=your_access_key" >&2
        echo "   OBS_SECRET_KEY=your_secret_key" >&2
        echo "   OBS_BUCKET_NAME=your_bucket_name" >&2
        echo "   OBS_ENDPOINT=obs.your-region.myhuaweicloud.com" >&2
        echo "   LOCAL_MOUNT_POINT=C:\\path\\to\\mount\\point" >&2
    fi
    exit 1
fi

if [ ! -r "$CONFIG_FILE" ]; then
    echo "错误: 配置文件 $CONFIG_FILE 不可读" >&2
    echo "请检查文件权限" >&2
    exit 1
fi

# 从配置文件中读取配置
echo "正在加载配置文件 $CONFIG_FILE..." >&2
source "$CONFIG_FILE" || {
    echo "错误: 加载配置文件 $CONFIG_FILE 失败" >&2
    echo "请检查文件内容格式是否正确" >&2
    if [[ "$(uname -s)" == "MINGW"* || "$(uname -s)" == "CYGWIN"* ]]; then
        echo "Windows用户提示: 请确保配置文件使用Unix(LF)换行格式" >&2
        echo "可以使用Notepad++等编辑器转换换行格式" >&2
    fi
    exit 1
}

# 检查必需配置参数
for var in OBS_ACCESS_KEY OBS_SECRET_KEY OBS_BUCKET_NAME OBS_ENDPOINT LOCAL_MOUNT_POINT; do
    if [ -z "${!var}" ]; then
        echo "错误: 必需配置参数 $var 未设置" >&2
        echo "请在配置文件中设置此参数" >&2
        exit 1
    fi
done

# 安装 s3fs 工具
install_s3fs() {
    if command -v s3fs &> /dev/null; then
        echo "s3fs 已安装"
    else
        echo "正在安装 s3fs..."
        if [ -f /etc/debian_version ]; then
            apt-get update -y
            apt-get install s3fs -y
        elif [ -f /etc/redhat-release ]; then
            yum install epel-release -y
            yum install s3fs-fuse -y
        elif [[ "$(uname -s)" == "MINGW"* || "$(uname -s)" == "CYGWIN"* ]]; then
            echo "Windows系统请手动安装s3fs并配置环境变量"
            exit 1
        else
            echo "不支持的操作系统发行版，请手动安装 s3fs"
            exit 1
        fi

        if ! command -v s3fs &> /dev/null; then
            echo "s3fs 安装失败，请手动安装"
            exit 1
        fi
    fi
}

# 创建挂载点
create_mount_point() {
    if [ ! -d "$LOCAL_MOUNT_POINT" ]; then
        mkdir -p "$LOCAL_MOUNT_POINT"
        if [ $? -ne 0 ]; then
            echo "创建挂载点 $LOCAL_MOUNT_POINT 失败"
            exit 1
        fi
    fi
}

# 配置认证信息
configure_auth() {
    echo "$OBS_ACCESS_KEY:$OBS_SECRET_KEY" > /etc/passwd-s3fs
    chmod 600 /etc/passwd-s3fs
    if [ $? -ne 0 ]; then
        echo "配置认证信息失败"
        exit 1
    fi
}

# 挂载 OBS 存储桶
mount_obs() {
    install_s3fs
    create_mount_point
    configure_auth
    # 捕获s3fs命令输出以便显示错误详情
    local cmd="s3fs $OBS_BUCKET_NAME $LOCAL_MOUNT_POINT -o passwd_file=/etc/passwd-s3fs -o url=http://$OBS_ENDPOINT"
    if [[ "$(uname -s)" == "MINGW"* || "$(uname -s)" == "CYGWIN"* ]]; then
        echo "Windows环境下请手动执行以下命令:"
        echo "$cmd"
        echo "请确保已正确安装s3fs并配置环境变量"
        exit 1
    else
        local output=$($cmd 2>&1)
        if [ $? -ne 0 ]; then
            echo "OBS 存储桶挂载失败，执行的命令:"
            echo "$cmd"
            echo "错误详情:"
            echo "$output"
            echo "请检查以下配置是否正确:"
            echo "1. OBS_ACCESS_KEY 和 OBS_SECRET_KEY"
            echo "2. OBS_BUCKET_NAME 和 OBS_ENDPOINT"
            echo "3. 挂载点目录 $LOCAL_MOUNT_POINT 是否存在且有写入权限"
            echo "4. 网络连接是否正常"
            echo "5. 防火墙设置是否允许访问OBS端点"
            echo "6. 当前用户是否有权限访问挂载点目录"
            exit 1
        fi
    fi
    # 检查挂载是否成功
    if mountpoint -q $LOCAL_MOUNT_POINT; then
        echo "OBS 存储桶 $OBS_BUCKET_NAME 已成功挂载到 $LOCAL_MOUNT_POINT"
    else
        echo "OBS 存储桶挂载失败，但s3fs命令未返回错误，请检查挂载点权限和配置"
        echo $cmd
        exit 1
    fi
}

# 卸载 OBS 存储桶
umount_obs() {
    # 检查挂载点是否存在
    if mountpoint -q $LOCAL_MOUNT_POINT; then
        umount $LOCAL_MOUNT_POINT
        if [ $? -eq 0 ]; then
            echo "OBS 存储桶已成功从 $LOCAL_MOUNT_POINT 卸载"
        else
            echo "卸载 OBS 存储桶失败，请检查是否有进程正在使用该挂载点"
            exit 1
        fi
    else
        echo "挂载点 $LOCAL_MOUNT_POINT 未挂载 OBS 存储桶"
    fi
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -f <path> 指定配置文件路径 (默认: $DEFAULT_CONFIG)"
    echo "  mount    挂载华为云 OBS 存储桶"
    echo "  umount   卸载华为云 OBS 存储桶"
    echo "  help     显示此帮助信息"
}

# 解析命令行参数
while getopts "f:" opt; do
    case "$opt" in
        f)
            CONFIG_FILE="$OPTARG"
            ;;
        ?)
            show_help
            exit 1
            ;;
    esac
done
shift $(($OPTIND - 1))

# 根据参数执行相应操作
case "$1" in
    mount)
        mount_obs
        ;;
    umount)
        umount_obs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "无效的参数，请使用 $0 help 查看帮助信息"
        exit 1
        ;;
esac