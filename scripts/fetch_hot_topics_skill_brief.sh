#!/usr/bin/env bash
# 供 cron / 本机：拉取「热点 + 每主题 N 篇参考文」JSON，可管道给撰写 Agent 或存盘。
# 用法：
#   export WERSS_BASE="http://127.0.0.1:8001"
#   export WERSS_USER="admin"
#   export WERSS_PASS="你的密码"
#   ./scripts/fetch_hot_topics_skill_brief.sh
# 可选：WERSS_TOKEN 已设则跳过密码登录；WERSS_ARTICLES_PER_TOPIC 默认 3

set -euo pipefail

BASE_URL="${WERSS_BASE:-http://127.0.0.1:8001}"
API_WX="${BASE_URL}/api/v1/wx"
PER_TOPIC="${WERSS_ARTICLES_PER_TOPIC:-3}"

# 有代理时避免把 localhost 走代理
export NO_PROXY="${NO_PROXY:+$NO_PROXY,}127.0.0.1,localhost"

if [[ -n "${WERSS_TOKEN:-}" ]]; then
  TOKEN="$WERSS_TOKEN"
else
  : "${WERSS_USER:?请设置 WERSS_USER 或 WERSS_TOKEN}"
  : "${WERSS_PASS:?请设置 WERSS_PASS 或 WERSS_TOKEN}"
  TOKEN="$(
    curl -sS --noproxy '*' -X POST "${API_WX}/auth/token" \
      -H 'Content-Type: application/x-www-form-urlencoded' \
      -d "username=${WERSS_USER}&password=${WERSS_PASS}" \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))"
  )"
  if [[ -z "$TOKEN" ]]; then
    echo "登录失败，请检查 WERSS_BASE / 用户名密码" >&2
    exit 1
  fi
fi

curl -sS --noproxy '*' \
  -H "Authorization: Bearer ${TOKEN}" \
  "${API_WX}/hot-topics/skill-brief?articles_per_topic=${PER_TOPIC}"

