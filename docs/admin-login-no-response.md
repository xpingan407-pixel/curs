# 企飞宝管理后台登录「点击无响应」

## 原因（2026-10-15）

1. **过期线路缓存**：`localStorage.api_base_url` 可能仍为 `api.yejhtf.com` / `api.nkihi.com` 等已失效域名，登录请求发到错误主机，表现为长时间加载或失败；错误提示在部分场景下不明显。
2. **账号 WS 在线**：管理端 `in=1` 登录时若该管理员在 App/WS 仍在线，接口返回「账号已在别处登录」；若前端未正确处理，体验像「点了没反应」。
3. **前端 catch 未提示**：`Login` 页 `catch` 仅 `console.error`，`applyLoginResult` 抛错（如权限）时无 Toast。

## 源站修复（202.95.14.138）

| 文件 | 改动 |
|------|------|
| `api.yejhtf.com/app/controller/Auth.php` | 管理后台登录时若 WS 在线则 `kickUser` 后允许登录，不再直接拒绝 |
| `web.yejhtf.com/assets/index-COizttuX.js` | 仅当 `api_base_url` 含 `api.tyyjeb.cn` 时才覆盖 `baseURL`；`applyLoginResult` 容错 |
| `web.yejhtf.com/assets/Login-DmC7nm_R.js` | 进入页清理无效 `api_base_url`；登录失败 Toast |
| `web.yejhtf.com/index.html` | 资源版本 `rejectack202610151952`（须与 `index-COizttuX.js` 等动态 import 的 `?v=` 一致，避免仍拉取带 `1200` 的损坏 chat 缓存） |
| `web.yejhtf.com/assets/*.js` | 凡引用 `chat-DSNVtjZy.js?v=` 的 chunk 统一为 `rejectack202610151952` |

## 后台空白 / `Unexpected token '{'`

若控制台报 `chat-DSNVtjZy.js?v=rejectack202610151200` 语法错误，多为浏览器或 CDN 仍缓存了曾损坏的 chat 包；源站 `chat-DSNVtjZy.js` 已修复且 `node --check` 通过。将全站 `?v=` 提到新 token 并强刷即可。

## 验收

1. 浏览器强刷 `https://web.tyyjeb.cn/login`（Ctrl+F5）。
2. 使用管理员账号登录，应跳转 `/dashboard` 或显示明确错误（密码错误 / 2FA）。
3. 开发者工具 Network 中 `POST https://api.tyyjeb.cn/login` 应为 200。
