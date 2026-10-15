# chat-DSNVtjZy.js fixes (2026-10-15)

## Symptom
Admin user `honguo` on web backend: switching customer chat always showed 孙建忠.

## Root cause (frontend Pinia chat store)
1. `handleGetChatHistorySuccess` used `else s=i` — keyed messages by `room_id` when chat item missing, while UI reads `messages[currentChatUser.id]`.
2. Stale `get_chat_history_success` could apply to wrong session without room guard.
3. `get_chat_list_success` synced `currentChatUser` with loose `room_id` compare only.
4. `setCurrentChatUser` held shared object reference from `chatList`.

## Changes applied on server
- `/www/wwwroot/web.yejhtf.com/assets/chat-DSNVtjZy.js`
- Cache bust: `rejectack202610151954` in `index.html` and **all** asset imports; mismatched `?v=` pulls cached broken chat → `Unexpected token '{'` at `setCurrentChatUser` (bad merge: `this.isConnected){` without `if (`).

## Deploy recipe (do not hand-merge `setCurrentChatUser`)

1. Restore `chat-DSNVtjZy.js.bak.20261015-1712-tyyjeb`
2. Apply **only** `handleGetChatHistorySuccess` guard (`room_id` mismatch → return; drop `else s=i`)
3. `node --check` on a `.mjs` copy before publishing
4. Bump unified `rejectack*` on all chunks

Do **not** replace `setCurrentChatUser` with comma-operator `t&&(..., this.isConnected){` — invalid JS.
