# UXIM 103.179.45.220 事件导出说明

| 文件 | 说明 |
|------|------|
| `uxim_attack_chat_private_pairs.csv` | 私聊被读取记录，793 行（含表头）；字段含主体用户、对方 `peer_key`、访问次数 |
| `uxim_attack_chat_group_rooms.csv` | 群聊 `room_id` 被读取记录，35 行 |
| `uxim_attack_compromised_admin_accounts.csv` | 失陷/恶意管理账号清单 |

数据来源：`api.hzjgh.com` Nginx 访问日志，攻击 IP `103.179.45.220`，HTTP 200 的 `GET /admin/users/{id}/chat/...`。

生成时间：2026-10-09（UTC）。
