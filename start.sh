#!/bin/bash
cd /app/
source install.sh

STAR_REPO_URL="https://github.com/letuswerss/werss"
STAR_PROMPT_MARKER="/app/data/.star_prompt_seen"

prompt_for_github_star() {
    if [ ! -t 0 ] || [ ! -t 1 ]; then
        return 0
    fi

    if [ -f "$STAR_PROMPT_MARKER" ]; then
        return 0
    fi

    mkdir -p "$(dirname "$STAR_PROMPT_MARKER")"

    echo ""
    echo "⭐ 如果这个项目对你有帮助，可以顺手点个 Star"
    read -p "现在打开 GitHub Star 页面吗？(Y/n，默认打开): " -n 1 -r
    echo

    local open_star_page=true
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        open_star_page=false
    fi

    if [ "$open_star_page" = true ]; then
        local star_done=false

        if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
            if gh repo star letuswerss/werss >/dev/null 2>&1; then
                star_done=true
                echo "已通过 gh 命令点 Star"
            fi
        fi

        if [ "$star_done" = false ]; then
            if command -v open >/dev/null 2>&1; then
                open "$STAR_REPO_URL" >/dev/null 2>&1 || true
            elif command -v xdg-open >/dev/null 2>&1; then
                xdg-open "$STAR_REPO_URL" >/dev/null 2>&1 || true
            else
                echo "请手动打开: $STAR_REPO_URL"
            fi
            echo "已尝试打开: $STAR_REPO_URL"
        fi

        touch "$STAR_PROMPT_MARKER"
    else
        echo "已跳过点 Star 提示，下次启动会继续询问"
    fi
    echo ""
}

# 与 init_sys.py 一致：优先 WERSS_*，兼容 USERNAME/PASSWORD（避免 .env 里只有 WERSS_* 时误报未设置）
_init_user="${WERSS_USERNAME:-${USERNAME:-}}"
_init_pass="${WERSS_PASSWORD:-${PASSWORD:-}}"
echo "=== 环境变量检查 ==="
if [ -n "${_init_user}" ]; then
    echo "登录用户名(生效): ${_init_user}"
else
    echo "登录用户名(生效): 未设置 → 默认 admin"
fi
if [ -n "${_init_pass}" ]; then
    echo "登录密码(生效): 已设置（长度: ${#_init_pass} 字符）"
else
    echo "登录密码(生效): 未设置 → 默认 admin@123"
fi
if [ -n "${DB}" ]; then
    echo "DB: 已设置"
else
    echo "DB: 未设置"
fi
echo "=================="

prompt_for_github_star

# Docker 环境默认执行初始化（init_user 会检查用户是否存在，存在则更新密码）
# 这样可以确保环境变量中的密码总是生效
python3 main.py -job True -init True
