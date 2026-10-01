#!/bin/bash
set -euo pipefail
CHAT_PHP="${1:-/www/wwwroot/uxim/app/controller/chat/Chat.php}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/patch-group-chat-fix.py" "$CHAT_PHP"
# Baota PHP 8.2 typical service name
if command -v bt >/dev/null 2>&1; then
  bt reload 2>/dev/null || true
fi
if systemctl is-active php-fpm-82 >/dev/null 2>&1; then
  systemctl reload php-fpm-82 || systemctl restart php-fpm-82
fi
echo "Done. Verify: curl -H \"Authorization: Bearer <token>\" https://api.dfkcg.top/auth/rooms"
