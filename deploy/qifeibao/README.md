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
- `/www/wwwroot/web.yejhtf.com` — Web
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
