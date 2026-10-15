# App 登录「节点未就绪」排查（企飞宝）

## 现象

App 启动/登录前会拉分发配置并对各线路做健康检查；全部失败时客户端提示 **「节点未就绪」**。

## 客户端逻辑（简要）

1. 固定请求 `https://api.joojop.com/config.json`（分发入口，写死在 App 内）。
2. 读取 `apis[].base_url`，对每个节点请求 **`/health`**（常见为 **GET**，需 JSON 且 `data.ready === true`；iOS 也可能发 **HEAD**）。
3. 任一线路可用后才用该 `base_url` 登录、`ws_url` 连 WS。

## 2026-10-15 实测结论

| 地址 | config.json | GET /health | POST /login |
|------|-------------|-------------|-------------|
| **CDN** `https://api.joojop.com` | **v12**（2026-08-27），三条线路为 joojop / yejhtf / nkihi | **404 HTML**（Next.js 注册站） | **404 HTML** |
| **源站** `Host: api.joojop.com` → `202.95.14.138` | **v18**，三条均为 `https://api.tyyjeb.cn` | `ready: true` JSON | 正常 ThinkPHP JSON |
| `https://api.tyyjeb.cn` | v18 | 正常 | 正常 |

公网 DNS：`api.joojop.com` → CNAME → **163.223.146.85**（CDN），**未回源**到企飞宝 API 机。

对 CDN 当前缓存的 **v12** 配置模拟探活：

- `https://api.joojop.com/health` GET → 404，无 `ready`
- `https://api.yejhtf.com` / `https://api.nkihi.com` → **DNS 无法解析**

因此 App 会认为 **所有节点不可用** → 「节点未就绪」。

源站 API（`/www/wwwroot/api.yejhtf.com`）与 `api.tyyjeb.cn` **本身正常**；问题在 **分发域名 CDN 缓存与回源策略**，不在 PHP/WS 进程。

## 修复建议（需 CDN/DNS 权限）

在 **defmewaskw / hongz（ywgmwh）CDN 面板**（脚本 `purge-joojop-config.sh` 中的说明）：

1. **刷新** `api.joojop.com` 的 `/config.json` 缓存；回源应指向 **202.95.14.138**，回源 Host **`api.joojop.com`**（源站 Nginx 已包含该 `server_name`）。
2. 将以下路径 **回源到 API 源站**（勿走 Next.js 注册站）：`/health`、`/config.json`、`/login`、`/auth/*`、`/ws` 等。
3. 或：将 `api.joojop.com` 解析 **A 记录直连 202.95.14.138**（绕过错误 CDN 站点）。

刷新成功后，公网 `curl https://api.joojop.com/config.json` 应看到 **version ≥ 18**、`apis[0].base_url` 为 **`https://api.tyyjeb.cn`**，且 `curl https://api.joojop.com/health` 返回 JSON `ready: true`。

## 源站自检命令

```bash
# 模拟 CDN 回源（在任意机器）
curl -sk --resolve api.joojop.com:443:202.95.14.138 https://api.joojop.com/health
curl -sk --resolve api.joojop.com:443:202.95.14.138 https://api.joojop.com/config.json
```

## 相关文件（源站 202.95.14.138）

- 动态配置：`app/controller/index/Index.php` → `config()` / `health()`
- 静态兜底：`public/config.json`（应与动态一致）
- 运维脚本：`/www/wwwroot/scripts/purge-joojop-config.sh`
