#!/bin/bash
# 企飞宝服务器远程命令。需: sshpass, QIFEIBAO_SSH_PASSWORD
set -euo pipefail
HOST="${QIFEIBAO_HOST:-202.95.14.138}"
PORT="${QIFEIBAO_SSH_PORT:-22}"
USER="${QIFEIBAO_SSH_USER:-root}"

if [ -z "${QIFEIBAO_SSH_PASSWORD:-}" ]; then
  echo "Set QIFEIBAO_SSH_PASSWORD (企飞宝 root SSH 密码)" >&2
  exit 1
fi

exec sshpass -p "$QIFEIBAO_SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -p "$PORT" "$USER@$HOST" "$@"
