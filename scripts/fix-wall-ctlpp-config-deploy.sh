#!/usr/bin/env bash
# 在入口机 207.56.20.191 上执行（需 root SSH）。
# 将 wall.ctlpp.com/config.json 与 uxim 源站线路对齐（含 api.tsafyw.cn）。
set -euo pipefail
WALL_ROOT="/www/wwwroot/wall.ctlpp.com"
SRC="${1:-/root/wall-ctlpp-config-v1-tsafyw.json}"
if [[ ! -f "$SRC" ]]; then
  echo "缺少配置 JSON: $SRC" >&2
  exit 1
fi
cp -a "${WALL_ROOT}/config.json" "${WALL_ROOT}/config.json.bak.$(date +%Y%m%d%H%M%S)"
install -m 644 "$SRC" "${WALL_ROOT}/config.json"
echo "已写入 ${WALL_ROOT}/config.json"
curl -fsS -H "Host: wall.ctlpp.com" "http://127.0.0.1/config.json" | python3 -c "import sys,json; d=json.load(sys.stdin); print('apis:', [a['base_url'] for a in d['apis']])"
