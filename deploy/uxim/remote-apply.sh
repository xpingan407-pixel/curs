#!/bin/bash
# Apply UXIM group-chat patch over SSH. Requires: sshpass, UXIM_SSH_PASSWORD
set -euo pipefail
HOST="${UXIM_SSH_HOST:-112.213.101.240}"
USER="${UXIM_SSH_USER:-root}"
CHAT_PHP="${UXIM_CHAT_PHP:-/www/wwwroot/uxim/app/controller/chat/Chat.php}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${UXIM_SSH_PASSWORD:-}" ]; then
  echo "Set UXIM_SSH_PASSWORD (root SSH password for $HOST)" >&2
  exit 1
fi

sshpass -p "$UXIM_SSH_PASSWORD" scp -o StrictHostKeyChecking=no \
  "$SCRIPT_DIR/patch-group-chat-fix.py" "$USER@$HOST:/tmp/patch-group-chat-fix.py"

sshpass -p "$UXIM_SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$USER@$HOST" \
  "python3 /tmp/patch-group-chat-fix.py '$CHAT_PHP' && (systemctl reload php-fpm-82 2>/dev/null || bt reload 2>/dev/null || true)"

echo "Patch applied on $HOST"
