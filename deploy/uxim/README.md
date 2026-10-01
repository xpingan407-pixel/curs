# UXIM 群聊闪退修复

## 原因

`Chat.php` 中 `getUserRooms()` 使用不存在的字段 `from_user`（应为 `sender_id`），导致用户存在群会话时 `GET /auth/rooms` 返回 500。`getRoomMembers()` 在 `joined_at` 为空时对 null 调用 `format()` 也会 500。

## 在 UXIM 服务器执行

```bash
cd /www/wwwroot/uxim   # 或你的仓库路径
curl -fsSL "https://raw.githubusercontent.com/xpingan407-pixel/curs/<branch>/deploy/uxim/patch-group-chat-fix.py" -o /tmp/patch-group-chat-fix.py
python3 /tmp/patch-group-chat-fix.py /www/wwwroot/uxim/app/controller/chat/Chat.php
# 重载 PHP
systemctl reload php-fpm-82 2>/dev/null || bt reload 2>/dev/null || true
```

或复制本目录后执行：

```bash
bash deploy/uxim/apply-on-server.sh /www/wwwroot/uxim/app/controller/chat/Chat.php
```

## 验证

```bash
# 需有效用户 Token
curl -s -H "Authorization: Bearer <token>" https://api.dfkcg.top/auth/rooms
# 应返回 HTTP 200 且 JSON success=true（有群时 data 非空）
```
