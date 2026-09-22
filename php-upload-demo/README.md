# PHP 图片上传 Demo

最小示例：一个 `index.php` 处理表单展示与上传逻辑，文件保存在 `uploads/`。

## 运行

需要 PHP 8.1+（使用了 `match` 与 `strict_types`）。

```bash
cd php-upload-demo
php -S localhost:8080
```

浏览器打开 http://localhost:8080

## 说明

- 表单字段名：`image`，`enctype="multipart/form-data"`
- 限制：最大 5MB；允许 MIME：`jpeg` / `png` / `gif` / `webp`
- 保存文件名：随机十六进制，避免覆盖与路径注入
- 生产环境还需：登录鉴权、速率限制、病毒扫描、对象存储等
