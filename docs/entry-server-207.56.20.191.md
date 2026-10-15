# 入口机 207.56.20.191（运维备忘）

**角色：** `wall.ctlpp.com` 静态配置、`api.joojop.com` 入口等。

> SSH/面板密码请保存在 Cursor Secrets，**勿提交 Git**。

## SSH

| 项 | 值 |
|----|-----|
| 地址 | `207.56.20.191` |
| 端口 | `22` |
| 用户 | `root` |
| 验证 | 2026-10-15 密码登录成功 |

## wall.ctlpp.com

- 配置路径：`/www/wwwroot/wall.ctlpp.com/config.json`
- 部署脚本（仓库）：`scripts/fix-wall-ctlpp-config-deploy.sh` + `scripts/wall-ctlpp-config-v1-tsafyw.json`
- 2026-10-15：已增加 API 线路 `https://api.tsafyw.cn`（备用线路4）

```bash
curl -fsS https://wall.ctlpp.com/config.json | jq '[.apis[].base_url]'
```
