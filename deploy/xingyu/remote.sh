#!/bin/bash
# 星语服务器远程命令。需: sshpass, XINGYU_SSH_PASSWORD
set -euo pipefail
HOST="${XINGYU_HOST:-206.119.118.249}"
PORT="${XINGYU_SSH_PORT:-17603}"
USER="${XINGYU_SSH_USER:-root}"

if [ -z "${XINGYU_SSH_PASSWORD:-}" ]; then
  echo "Set XINGYU_SSH_PASSWORD (星语 root SSH 密码)" >&2
  exit 1
fi

exec sshpass -p "$XINGYU_SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -p "$PORT" "$USER@$HOST" "$@"
