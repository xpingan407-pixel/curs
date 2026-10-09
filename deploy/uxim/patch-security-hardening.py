#!/usr/bin/env python3
"""Apply UXIM security hardening against mass registration / admin abuse."""
from __future__ import annotations

import sys
from pathlib import Path

BLOCKED_IP_MIDDLEWARE = """<?php
namespace app\\middleware;

use app\\common\\Helper;
use think\\facade\\Env;
use think\\Request;

class BlockedIp
{
    public function handle(Request $request, \\Closure $next)
    {
        $ip = Helper::getClientIP($request);
        $blocked = array_filter(array_map('trim', explode(',', (string) Env::get('BLOCKED_IPS', '103.179.45.220'))));
        if ($ip !== '' && in_array($ip, $blocked, true)) {
            return json([
                'success' => false,
                'message' => '访问被拒绝',
                'code' => 403,
            ], 403);
        }
        if ($request->url() && str_contains($request->url(), '..')) {
            return json([
                'success' => false,
                'message' => '非法请求路径',
                'code' => 400,
            ], 400);
        }
        return $next($request);
    }
}
"""

REGISTER_RATE = """
        // 注册 IP 限流（防批量注册）
        if (!\\app\\service\\RateLimitService::isAllowed('register_ip_' . $clientIP, 10, 3600)) {
            return Helper::response(false, '当前IP注册过于频繁，请稍后重试', null, 429);
        }
"""

INVITE_VALIDATE = """
        if (!preg_match('/^[A-Za-z0-9]{1,8}$/', $data['invite_code'])) {
            return Helper::response(false, '邀请码格式无效', null, 400);
        }

"""

ADMIN_2FA_REQUIRE = """
            if (!$twoFactorEnabled && in_array(($user->role ?? 'normal'), ['admin', 'super_admin', 'master_admin'], true)) {
                return Helper::response(false, '管理端登录必须先启用谷歌验证器', null, 403);
            }
"""


def patch_file(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text()
    if new.strip() in text:
        print(f"skip {label} (already applied)")
        return
    if old not in text:
        raise SystemExit(f"patch anchor missing for {label} in {path}")
    path.write_text(text.replace(old, new, 1))
    print(f"patched {label}")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/www/wwwroot/uxim")
    auth = root / "app/controller/Auth.php"
    user_admin = root / "app/controller/admin/User.php"
    middleware_php = root / "app/middleware.php"
    blocked = root / "app/middleware/BlockedIp.php"
    env_path = root / ".env"

    blocked.write_text(BLOCKED_IP_MIDDLEWARE)
    print(f"wrote {blocked}")

    patch_file(
        auth,
        "        // [cancelled 2026-08-22] register IP rate limit removed\n        // 格式校验",
        REGISTER_RATE + "        // 格式校验",
        "register rate limit",
    )
    patch_file(
        auth,
        "        if (!Helper::validatePassword($data['password'])) {\n            return Helper::response(false, '密码不能少于6位', null, 400);\n        }\n\n        $invite = InviteCode::where('code', $data['invite_code'])",
        "        if (!Helper::validatePassword($data['password'])) {\n            return Helper::response(false, '密码不能少于6位', null, 400);\n        }\n"
        + INVITE_VALIDATE
        + "        $invite = InviteCode::where('code', $data['invite_code'])",
        "invite code format",
    )
    patch_file(
        auth,
        "            if ($twoFactorEnabled) {\n                $totpCode = $this->normalizeTotpCode($data['totp_code'] ?? '');",
        "            if (!$twoFactorEnabled && in_array(($user->role ?? 'normal'), ['admin', 'super_admin', 'master_admin'], true)) {\n                return Helper::response(false, '管理端登录必须先启用谷歌验证器', null, 403);\n            }\n            if ($twoFactorEnabled) {\n                $totpCode = $this->normalizeTotpCode($data['totp_code'] ?? '');",
        "admin 2FA required",
    )

    patch_file(
        user_admin,
        "        $page = Request::param('page', 1);\n        $limit = Request::param('limit', 10);",
        "        $page = max(1, (int) Request::param('page', 1));\n        $limit = (int) Request::param('limit', 10);\n        if ($limit < 1) {\n            $limit = 10;\n        }\n        if ($limit > 100) {\n            $limit = 100;\n        }",
        "admin user list limit cap",
    )

    mw = middleware_php.read_text()
    entry = "    \\app\\middleware\\BlockedIp::class,"
    if entry not in mw:
        mw = mw.replace(
            "    \\think\\middleware\\AllowCrossDomain::class,",
            entry + "\n    \\think\\middleware\\AllowCrossDomain::class,",
        )
        middleware_php.write_text(mw)
        print("patched middleware.php")
    else:
        print("skip middleware.php")

    env_text = env_path.read_text()
    if "BLOCKED_IPS" not in env_text:
        env_path.write_text(env_text.rstrip() + "\nBLOCKED_IPS=103.179.45.220\n")
        print("appended BLOCKED_IPS to .env")
    else:
        print("skip .env BLOCKED_IPS")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
