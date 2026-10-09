# 星语（Star-Yu）运维连接

| 项 | 值 |
|----|-----|
| 备注 | **星语** |
| 主机 | `206.119.118.249` |
| SSH 端口 | `17603` |
| 用户 | `root` |
| 应用目录 | `/www/wwwroot/my-im` |
| 业务库 | MySQL `p-db`（IM 用户表 `im_user`） |

## SSH

本环境已配置别名（仅本机 `~/.ssh/config`）：

```bash
ssh xingyu   # HostName 206.119.118.249, Port 17603
```

密码请通过环境变量传入，**不要写入仓库**：

```bash
export XINGYU_SSH_PASSWORD='…'
sshpass -p "$XINGYU_SSH_PASSWORD" ssh -p 17603 root@206.119.118.249
```

或使用 `deploy/xingyu/remote.sh`（读取 `XINGYU_SSH_PASSWORD`）。

## 服务（systemd）

- `im-platform.service` — App API（`im-platform.jar`）
- `im-server.service` — WebSocket
- `im-biz.service` / `im-admin.service`

对象存储：`application-prod.yml` 中 `minio.domain`（如 `https://jovik.bgznp.com/file`）。
