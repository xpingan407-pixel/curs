<?php
declare(strict_types=1);

const UPLOAD_DIR = __DIR__ . '/uploads';
const MAX_BYTES = 5 * 1024 * 1024; // 5 MB
const ALLOWED_MIME = [
    'image/jpeg' => 'jpg',
    'image/png'  => 'png',
    'image/gif'  => 'gif',
    'image/webp' => 'webp',
];

$messages = [];
$uploadedUrl = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_FILES['image']) || !is_array($_FILES['image'])) {
        $messages[] = ['error', '未收到上传文件。'];
    } else {
        $file = $_FILES['image'];

        if ($file['error'] !== UPLOAD_ERR_OK) {
            $messages[] = ['error', uploadErrorMessage((int) $file['error'])];
        } elseif ($file['size'] > MAX_BYTES) {
            $messages[] = ['error', '文件超过 5MB 限制。'];
        } else {
            $finfo = new finfo(FILEINFO_MIME_TYPE);
            $mime = $finfo->file($file['tmp_name']);

            if ($mime === false || !isset(ALLOWED_MIME[$mime])) {
                $messages[] = ['error', '仅支持 JPG、PNG、GIF、WEBP 图片。'];
            } else {
                if (!is_dir(UPLOAD_DIR) && !mkdir(UPLOAD_DIR, 0755, true)) {
                    $messages[] = ['error', '无法创建上传目录。'];
                } else {
                    $ext = ALLOWED_MIME[$mime];
                    $basename = bin2hex(random_bytes(16)) . '.' . $ext;
                    $dest = UPLOAD_DIR . '/' . $basename;

                    if (!move_uploaded_file($file['tmp_name'], $dest)) {
                        $messages[] = ['error', '保存文件失败。'];
                    } else {
                        $uploadedUrl = 'uploads/' . $basename;
                        $messages[] = ['success', '上传成功：' . htmlspecialchars($basename, ENT_QUOTES, 'UTF-8')];
                    }
                }
            }
        }
    }
}

function uploadErrorMessage(int $code): string
{
    return match ($code) {
        UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE => '文件太大。',
        UPLOAD_ERR_PARTIAL => '文件只上传了一部分。',
        UPLOAD_ERR_NO_FILE => '请选择要上传的图片。',
        UPLOAD_ERR_NO_TMP_DIR => '服务器缺少临时目录。',
        UPLOAD_ERR_CANT_WRITE => '无法写入磁盘。',
        UPLOAD_ERR_EXTENSION => '扩展阻止了上传。',
        default => '上传失败（错误码 ' . $code . '）。',
    };
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PHP 图片上传 Demo</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 32rem; margin: 2rem auto; padding: 0 1rem; }
        .msg { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
        .msg.error { background: #fee; color: #900; }
        .msg.success { background: #efe; color: #060; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
        input[type="file"] { margin-bottom: 1rem; }
        button { padding: 0.5rem 1.25rem; cursor: pointer; }
        img.preview { max-width: 100%; margin-top: 1rem; border: 1px solid #ddd; border-radius: 4px; }
        code { font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>PHP 图片上传 Demo</h1>
    <p>单文件上传，服务端用 <code>finfo</code> 校验 MIME，保存到 <code>uploads/</code>。</p>

    <?php foreach ($messages as [$type, $text]): ?>
        <div class="msg <?= htmlspecialchars($type, ENT_QUOTES, 'UTF-8') ?>">
            <?= $text ?>
        </div>
    <?php endforeach; ?>

    <form method="post" enctype="multipart/form-data">
        <label for="image">选择图片（≤ 5MB）</label>
        <input type="file" name="image" id="image" accept="image/jpeg,image/png,image/gif,image/webp" required>
        <button type="submit">上传</button>
    </form>

    <?php if ($uploadedUrl !== null): ?>
        <p>预览：</p>
        <img class="preview" src="<?= htmlspecialchars($uploadedUrl, ENT_QUOTES, 'UTF-8') ?>" alt="已上传图片">
    <?php endif; ?>
</body>
</html>
