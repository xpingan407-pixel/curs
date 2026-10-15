# App 登录「节点未就绪」排查（企飞宝）

## 现象

App 启动/登录前会拉分发配置并对各线路做健康检查；全部失败时客户端提示 **「节点未就绪」**。

## 客户端逻辑（简要）

1. 固定请求 `https://api.joojop.com/config.json`（分发入口，写死在 App 内）。
2. 读取 `apis[].base_url`，对每个节点请求 **`/health`**（常见为 **GET**，需 JSON 且 `data.ready === true`；iOS 也可能发 **HEAD**）。
3. 任一线路可用后才用该 `base_url` 登录、`ws_url` 连 WS。

## 2026-10-15 实测结论（以公网 `api.joojop.com` 为准）

| 地址 | config.json | GET /health | 是否打到源站日志 |
|------|-------------|-------------|------------------|
| **公网 CDN** `https://api.joojop.com` | **v12**（2026-08-27），线路 joojop / yejhtf / nkihi | **404 HTML**（Next.js 注册站） | **否** |
| **入口机** `207.56.20.191` Host `api.joojop.com` | 静态 **v12** | Next.js 404 | — |
| **源站** `202.95.14.138` Host `api.joojop.com` | **v18**，线路均为 `api.tyyjeb.cn` | `ready: true` JSON | 是（仅直连/tyyjeb CDN 回源时） |
| `https://api.tyyjeb.cn` | v18 | 正常 | 是 |

公网 DNS：`api.joojop.com` → CNAME `*.hongz.ywgmwh.com` → 边缘 **163.223.146.85**。  
`api.tyyjeb.cn` 与 `api.joojop.com` 同属 hongz CDN，但 **joojop 站点仍回源入口机 `207.56.20.191`**，未像 tyyjeb 一样回源 **202.95.14.138**。

对公网 **v12** 配置模拟探活：

- `https://api.joojop.com/health` → 404，无 `ready`
- `https://api.yejhtf.com` / `https://api.nkihi.com` → **DNS 无法解析**

因此 App 会认为 **所有节点不可用** → 「节点未就绪」。源站 PHP/WS 正常，问题在 **joojop 的 CDN/入口链路**。

## 源站已做（202.95.14.138）

1. Nginx `server_name` 已含 `api.joojop.com`；`/config.json`、`/health` 由 PHP 动态输出 v18。
2. **HTTP 回源免 301**：对 `/config.json`、`/health`、`/ws`、`/auth/`、`/login` 等，80 端口不再强制跳转到公网 HTTPS（避免 CDN HTTP 回源时 301 到 CDN 边缘形成死循环）。备份：`api.yejhtf.com.conf.bak.joojop-http-origin-*`。
3. 脚本：
   - `scripts/purge-joojop-config.sh` — 对比公网 joojop 与源站 tyyjeb
   - `scripts/fix-joojop-entry-deploy.sh` — 在 **入口机** 上执行，将 config/health/auth/ws 反代到源站

自检（源站 HTTP 回源，与 CDN 改源后一致）：

```bash
curl -fsS http://202.95.14.138/config.json -H "Host: api.joojop.com"
curl -fsS http://202.95.14.138/health -H "Host: api.joojop.com"
```

## 必须完成的运维动作（闭环公网 joojop）

任选其一（推荐 A）：

### 方案 A：CDN 与 `api.tyyjeb.cn` 对齐（推荐）

在 **defmewaskw / hongz（ywgmwh）CDN 面板** 修改站点 `api.joojop.com`：

| 项 | 值 |
|----|-----|
| 回源 IP | `202.95.14.138` |
| 回源协议/端口 | HTTP `80` |
| 回源 Host | `api.joojop.com`（或 `api.tyyjeb.cn`） |
| 缓存 | `/config.json`、`/health`、`/auth/*`、`/ws` **不缓存** |
| 操作 | 刷新 `/config.json`；`PURGE` API 当前返回 **403**（无权限时需面板手动刷新） |

验收：

```bash
curl -fsS https://api.joojop.com/config.json | jq .version,.apis[0].base_url
curl -fsS https://api.joojop.com/health | jq .data.ready
```

应得到 **version ≥ 18**、`base_url` = `https://api.tyyjeb.cn`、`ready: true`。

### 方案 B：修复入口机 `207.56.20.191`

需 **root SSH**（当前源站密钥无法登录）。登录后执行：

```bash
bash /www/wwwroot/scripts/fix-joojop-entry-deploy.sh
```

（可将该脚本从源站 `scp` 到入口机，或在入口机按脚本内容手工配置 nginx。）然后在 CDN 面板 **刷新** `api.joojop.com` 的 `/config.json`。

### 方案 C：DNS A 记录直连源站

`api.joojop.com` → A `202.95.14.138`（julydns），且源站需为 `api.joojop.com` 签发有效 TLS 证书（当前证书 SAN 仅 `api.hxcci.com`）。

## 相关文件（源站）

- 动态配置：`/www/wwwroot/api.yejhtf.com/app/controller/index/Index.php`
- Nginx：`/www/server/panel/vhost/nginx/api.yejhtf.com.conf`
- 运维脚本：`/www/wwwroot/scripts/purge-joojop-config.sh`、`fix-joojop-entry-deploy.sh`
