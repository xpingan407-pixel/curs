# 企飞宝运维连接

| 项 | 值 |
|----|-----|
| 备注 | **企飞宝** |
| 主机 | `202.95.14.138` |
| SSH 端口 | `22` |
| 用户 | `root` |
| 主机名 | `I04-A28`（以实际 `hostname` 为准） |

## 主要目录（探测快照）

- `/www/wwwroot/api.yejhtf.com` — API 站点
- `/www/wwwroot/web.yejhtf.com` — **管理后台**静态站点（Vue）
- `/www/wwwroot/Foxim-go-ws` — Go WebSocket
- `UXIM-修改记录.md` — 变更记录

## SSH

本机别名（`~/.ssh/config`）：

```bash
ssh qifeibao
```

密码使用环境变量，**勿提交到 Git**：

```bash
export QIFEIBAO_SSH_PASSWORD='…'
./deploy/qifeibao/remote.sh 'hostname'
```

## 服务

- **nginx**：active（80 / 443 / 8088）
- **php-fpm-82**：active

## 源站 IP 白名单（ufw）

用户/运维 IP 可在源站 `202.95.14.138` 上放行（示例）：

```bash
ufw allow from 171.225.203.215 comment 'yejhtf-user-whitelist-YYYYMMDD'
```

说明：`web.yejhtf.com` 公网走 CDN，**仅源站 ufw 加白不能替代 CDN 侧放行**；若仍打不开后台，需在 CDN（`ywgmwh` / `163.223.146.x`）同步加白或查地域策略。

## 管理后台域名

| 域名 | 源站 nginx | 站点根目录 | API（前端写死） |
|------|------------|------------|-----------------|
| `web.yejhtf.com` | `web.yejhtf.com.conf` | `/www/wwwroot/web.yejhtf.com` | `https://api.yejhtf.com` |
| `bruzibot.cn` / `www.bruzibot.cn` | `bruzibot.cn.conf` | 同上（共用后台包） | 同上 |

源站已绑定 `bruzibot.cn`：`server_name bruzibot.cn www.bruzibot.cn`，`root` 指向 `web.yejhtf.com` 目录。API 侧 `config/cors.php` 与 `Index::config()` 的 `webAdminOrigins` 已加入 `https://bruzibot.cn`、`https://www.bruzibot.cn`。

公网 `bruzibot.cn` 解析到与 `web.yejhtf.com` 相同的 CDN（`ywgmwh`）。若 HTTPS 出现 **502**，需在 CDN 控制台为该域名添加加速并回源 `202.95.14.138:80`，回源 Host 使用 `bruzibot.cn`（或与源站 `server_name` 一致）。
