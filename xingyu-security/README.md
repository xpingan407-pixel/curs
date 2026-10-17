# 星语安全加固包（扫描封禁 + 风险统计）

无法在公网直接推送至 `206.119.118.249` 时，请用 **im-prod-root 私钥**从运维 IP（如 `113.5.87.189`）登录后部署。

## 快速部署

```bash
# 将本目录上传到服务器，例如 /root/xingyu-security
cd /root/xingyu-security/scripts
chmod +x install-scan-defense.sh

# 可选：多个运维 IP
export HZ_SSH_ALLOW_IPS="113.5.87.189 1.2.3.4"

sudo ./install-scan-defense.sh install
```

## 文档

- [BUG 与风险统计](docs/星语-BUG与风险统计.md)
- [异常扫描封禁策略](docs/异常扫描封禁策略.md)

## 注意

- 安装脚本中的 `02-hz-scan-drop-server.conf` 可能与现有 `00-default-deny` 冲突，部署后务必 `nginx -t` 并抽测 `/api/line/ping`。
- CDN 回源 IP 变更时更新 `jail.d` 内 `ignoreip`。
