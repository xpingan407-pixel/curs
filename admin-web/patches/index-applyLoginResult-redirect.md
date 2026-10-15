# 登录成功不跳转（applyLoginResult 阻塞）

## 原因

`applyLoginResult` 在写入 token 后 **`await` Vite 预加载链** 拉取 `chat-DSNVtjZy.js` 再 `connect()`。若 chat 或其依赖加载慢/卡住，`login()` 一直 pending，Login 页不会执行 `router.push/replace('/dashboard')`，表现为接口已 200「登录成功」但页面停在登录页。

## 修复（源站 `index-COizttuX.js`）

1. 先设置 `token` / `userInfo` / `localStorage`。
2. `role` 使用 `(e.user && e.user.role) || e.role`。
3. 管理员 chat：`import(...).then(connect)` **不 await**（失败仅 `console.error`）。
4. `Login-DmC7nm_R.js`：`await router.replace('/dashboard')`。

缓存版本：`rejectack202610151954`（与 `index.html` 一致）。
