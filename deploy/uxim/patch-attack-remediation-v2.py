#!/usr/bin/env python3
"""UXIM incident remediation v2: close chat IDOR, tighten admin access, rate limits."""
from __future__ import annotations

import sys
from pathlib import Path

ADMIN_RATE_LIMIT = """<?php
namespace app\\middleware;

use app\\common\\Helper;
use app\\service\\RateLimitService;

class AdminRateLimit
{
    public function handle($request, \\Closure $next)
    {
        $uid = (int) ($request->user_id ?? 0);
        $ip = Helper::getClientIP($request);
        $key = $uid > 0 ? ('admin_api_uid_' . $uid) : ('admin_api_ip_' . $ip);
        if (!RateLimitService::isAllowed($key, 120, 60)) {
            return json([
                'success' => false,
                'message' => '操作过于频繁，请稍后再试',
                'code' => 429,
            ], 429);
        }
        return $next($request);
    }
}
"""


def patch_file(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text()
    if new.strip() in text:
        print(f"skip {label}")
        return
    if old not in text:
        raise SystemExit(f"anchor missing: {label} in {path}")
    path.write_text(text.replace(old, new, 1))
    print(f"patched {label}")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/www/wwwroot/uxim")
    user = root / "app/controller/admin/User.php"
    admin_auth = root / "app/middleware/AdminAuth.php"
    auth = root / "app/controller/Auth.php"
    blocked = root / "app/middleware/BlockedIp.php"
    route = root / "route/app.php"
    admin_rate = root / "app/middleware/AdminRateLimit.php"

    admin_rate.write_text(ADMIN_RATE_LIMIT)
    print(f"wrote {admin_rate}")

    patch_file(
        blocked,
        '        if ($request->url() && str_contains($request->url(), \'..\')) {',
        '        $path = strtolower((string) $request->url());\n'
        '        if (str_contains($path, \'..\') || str_contains($path, \'%2e%2e\') || str_contains($path, \'%252e\')) {',
        "blocked path encoding",
    )

    patch_file(
        admin_auth,
        "        if ($user->status != 1) {\n"
        "            return json([\n"
        "                'success' => false,\n"
        "                'message' => '账号已被禁用',\n"
        "            ], 403);\n"
        "        }\n"
        "        \n"
        "        // 将用户信息存储到请求中",
        "        if ($user->status != 1) {\n"
        "            return json([\n"
        "                'success' => false,\n"
        "                'message' => '账号已被禁用',\n"
        "            ], 403);\n"
        "        }\n"
        "\n"
        "        if ((int)($user->google2fa_enabled ?? 0) !== 1 || empty($user->google2fa_secret)) {\n"
        "            return json([\n"
        "                'success' => false,\n"
        "                'message' => '管理端必须启用谷歌验证器',\n"
        "            ], 403);\n"
        "        }\n"
        "        \n"
        "        // 将用户信息存储到请求中",
        "admin route requires 2FA",
    )

    patch_file(
        user,
        "        // 允许查看互为好友的用户设备（会话详情等场景）\n"
        "        $isFriend = Friend::where(function ($q) use ($currentAdminId, $targetUserId) {\n"
        "            $q->where('user_id', $currentAdminId)->where('friend_id', $targetUserId);\n"
        "        })->whereOr(function ($q) use ($currentAdminId, $targetUserId) {\n"
        "            $q->where('user_id', $targetUserId)->where('friend_id', $currentAdminId);\n"
        "        })->find();\n"
        "        if ($isFriend) {\n"
        "            return true;\n"
        "        }\n"
        "\n",
        "",
        "remove friend checkAccess bypass",
    )

    patch_file(
        user,
        "    public function update($id)\n    {\n        if (!is_numeric($id)) {\n            return Helper::response(false, '无效的用户ID');\n        }",
        "    public function update($id)\n    {\n        if (!is_numeric($id)) {\n            return Helper::response(false, '无效的用户ID');\n        }\n        $id = (int) $id;",
        "cast user id int on update",
    )

    patch_file(
        user,
        "        $user->save();\n\n        // 改密后只踢 WS，不清理 Token、不写 Redis",
        "        $user->save();\n\n        if ($passwordChanged) {\n            \\app\\service\\JwtService::clearCurrentJti((string) $user->id);\n        }\n\n        // 改密后只踢 WS，不清理 Token、不写 Redis",
        "jwt clear on admin password change",
    )

    patch_file(
        user,
        "use app\\model\\Friend;\nuse think\\facade\\Request;",
        "use app\\model\\Friend;\nuse app\\model\\ChatRoomMember;\nuse think\\facade\\Request;",
        "import ChatRoomMember",
    )

    patch_file(
        user,
        "    public function chatHistory($id, $friend_id)\n    {\n        if (!$this->checkAccess($id)) {\n            return Helper::response(false, '无权访问该用户数据');\n        }\n\n        $page = (int)Request::param('page', 1);",
        "    public function chatHistory($id, $friend_id)\n    {\n        if (!is_numeric($id)) {\n            return Helper::response(false, '无效的用户ID');\n        }\n        $id = (int) $id;\n        $friend_id = is_string($friend_id) ? urldecode($friend_id) : (string) $friend_id;\n        if (str_contains($friend_id, \"'\") || stripos($friend_id, 'sleep(') !== false) {\n            return Helper::response(false, '非法请求');\n        }\n        if (!\\app\\service\\RateLimitService::isAllowed('admin_chat_' . ($this->request->user_id ?? 0), 60, 60)) {\n            return Helper::response(false, '请求过于频繁', null, 429);\n        }\n        if (!$this->checkAccess($id)) {\n            return Helper::response(false, '无权访问该用户数据');\n        }\n\n        $page = (int)Request::param('page', 1);",
        "chatHistory rate limit and input guard",
    )

    patch_file(
        user,
        "            $roomId = \"{$minId}_{$maxId}\";\n        }\n\n        $query = \\app\\model\\ChatMessage::alias('m')",
        "            $roomId = \"{$minId}_{$maxId}\";\n"
        "            $fid = (int) $friend_id;\n"
        "            $friendOk = Friend::where('user_id', $id)->where('friend_id', $fid)->find()\n"
        "                ?: Friend::where('user_id', $fid)->where('friend_id', $id)->find();\n"
        "            if (!$friendOk) {\n"
        "                return Helper::response(false, '无权查看该会话');\n"
        "            }\n"
        "        }\n\n"
        "        if ($isGroup || str_starts_with($friend_id, 'room_')) {\n"
        "            if (!ChatRoomMember::where('room_id', $roomId)->where('user_id', $id)->find()) {\n"
        "                return Helper::response(false, '无权查看该群聊');\n"
        "            }\n"
        "        }\n\n"
        "        $query = \\app\\model\\ChatMessage::alias('m')",
        "chatHistory friend and group membership",
    )

    patch_file(
        auth,
        "        // 1. IP 维度限流防刷 (15分钟50次)\n"
        "        if (!\\app\\service\\RateLimitService::isAllowed('login_ip_' . $clientIP, 50, 900)) {\n"
        "            return Helper::response(false, '当前IP登录过于频繁，请稍后重试', [], 429);\n        }",
        "        // 1. IP 维度限流防刷 (15分钟50次)\n"
        "        if (!\\app\\service\\RateLimitService::isAllowed('login_ip_' . $clientIP, 50, 900)) {\n"
        "            return Helper::response(false, '当前IP登录过于频繁，请稍后重试', [], 429);\n"
        "        }\n"
        "        if (isset($data['in']) && (int) $data['in'] === 1) {\n"
        "            if (!\\app\\service\\RateLimitService::isAllowed('admin_login_ip_' . $clientIP, 20, 900)) {\n"
        "                return Helper::response(false, '管理端登录过于频繁，请稍后重试', [], 429);\n"
        "            }\n"
        "        }",
        "admin login IP rate limit",
    )

    patch_file(
        auth,
        "        if ($twoFactorToken === '' || $totpCode === '') {\n"
        "            return Helper::response(false, '请求参数错误'.$data['two_factor_token'].$data['totp_code']);\n"
        "        }",
        "        if ($twoFactorToken === '' || $totpCode === '') {\n"
        "            return Helper::response(false, '请求参数错误');\n"
        "        }",
        "login2fa error sanitization",
    )

    route_text = route.read_text()
    old_mw = "})->middleware([\\app\\middleware\\Auth::class, \\app\\middleware\\AdminAuth::class]);"
    new_mw = "})->middleware([\n    \\app\\middleware\\Auth::class,\n    \\app\\middleware\\AdminAuth::class,\n    \\app\\middleware\\AdminRateLimit::class,\n]);"
    if "AdminRateLimit" not in route_text:
        if old_mw not in route_text:
            raise SystemExit("route middleware anchor missing")
        route.write_text(route_text.replace(old_mw, new_mw, 1))
        print("patched route admin middleware")
    else:
        print("skip route")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
