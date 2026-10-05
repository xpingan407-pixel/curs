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
