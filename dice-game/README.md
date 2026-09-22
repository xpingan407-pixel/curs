# 三骰猜大小（UniApp + PHP）

三颗骰子，玩家押 **大 / 小 / 单 / 双**，PHP 开奖，UniApp 前端展示。

## 目录

- `backend/api.php` — 游戏 API（初始化、状态、下注开奖）
- `uniapp/` — UniApp（Vue 3）前端，用 HBuilderX 或 `@dcloudio/vite-plugin-uni` 运行

## 规则摘要

| 玩法 | 条件 |
|------|------|
| 大 | 三骰总和 11～17 |
| 小 | 三骰总和 4～10 |
| 单 | 总和为奇数 |
| 双 | 总和为偶数 |

- **豹子**（三颗相同）：押大/小/单/双均判负  
- 总和 **3** 或 **18**：押大、押小判负（围骰）  
- 赔率 **1:1**，初始筹码 **10000**，单注 **10～5000**

## 启动后端

```bash
cd backend
php -S 0.0.0.0:8080
```

接口示例：

- `GET /api.php?action=init` — 新建会话，返回 `token` 与余额  
- `GET /api.php?action=status` — 请求头 `X-Game-Token`  
- `POST /api.php?action=play` — JSON：`{"betType":"big|small|odd|even","amount":100}`

玩家数据保存在 `backend/data/*.json`。

## 启动前端

1. 用 **HBuilderX** 打开 `uniapp` 目录，运行到浏览器或微信开发者工具。  
2. 修改 `uniapp/utils/config.js` 中的 `API_BASE`：  
   - H5 本机：`http://localhost:8080/api.php`  
   - 真机调试：改成电脑局域网 IP，例如 `http://192.168.1.8:8080/api.php`  
3. 小程序需在后台配置 **request 合法域名**；开发阶段可在开发者工具中关闭域名校验。

## 技术说明

- 跨域：API 已设置 `Access-Control-Allow-Origin: *`  
- 会话：`init` 返回 32 位 hex `token`，客户端存本地并随请求携带 `X-Game-Token`
