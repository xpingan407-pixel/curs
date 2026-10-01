# UXIM 群聊 / 群内图片修复

## 原因（群内收不到图、闪退）

1. **`GET /auth/rooms` 返回 500**：`getUserRooms()` 未读数查询使用不存在的字段 `from_user`（应为 `sender_id`）。用户一旦加入群，会话列表拉取失败，客户端无法同步群会话与图片消息。
2. **`GET /auth/rooms/{id}/members` 500**：`joined_at` 为空时对 null 调用 `format()`。
3. **会话列表最后一条为图片时**：`content_raw` 对 URL 做 `htmlspecialchars`，部分客户端用 `content_raw` 渲染缩略图会失败（已改为图片/视频类型保留原始 URL）。

图片文件本身在 OSS（`aliyunoss.bsafjkf.cn/chat/...`）上传与 WS 推送经实测正常；问题主要在 **群会话 HTTP 接口崩溃 + 列表预览字段**。

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
