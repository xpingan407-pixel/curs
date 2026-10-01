#!/usr/bin/env python3
"""
Patch UXIM Chat.php: fix group chat 500 on GET /auth/rooms and GET /auth/rooms/{id}/members.

Run on the UXIM app server:
  python3 patch-group-chat-fix.py /www/wwwroot/uxim/app/controller/chat/Chat.php
"""
from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

UNREAD_BLOCK_OLD = """            // 获取未读消息数
            $unreadCount = ChatMessage::where('room_id', $userRoom->room_id)
                ->where('from_user', '<>', $userID)
                ->where('created_at', '>', $userRoom->joined_at)
                ->count();"""

UNREAD_BLOCK_NEW = """            // 获取未读消息数
            $excludeSenderId = ($currentUser && isset($currentUser->id))
                ? (int) $currentUser->id
                : (int) (User::where('user_id', $userID)->value('id') ?: 0);
            $unreadQuery = ChatMessage::where('room_id', $userRoom->room_id)
                ->where('sender_id', '<>', $excludeSenderId);
            if ($userRoom->joined_at) {
                $unreadQuery->where('created_at', '>', $userRoom->joined_at);
            }
            $unreadCount = $unreadQuery->count();"""


def patch_unread_block(content: str) -> str:
    if UNREAD_BLOCK_NEW.strip() in content:
        return content
    # Already fixed in a previous run / manual edit
    if (
        "excludeSenderId" in content
        and "->where('sender_id'" in content
        and "->where('from_user'" not in content
    ):
        return content
    if UNREAD_BLOCK_OLD in content:
        return content.replace(UNREAD_BLOCK_OLD, UNREAD_BLOCK_NEW)

    # Indentation-tolerant fallback for the bad column name
    old = "->where('from_user', '<>', $userID)"
    if old not in content:
        raise SystemExit("Unread block not found (already patched or Chat.php changed).")

    # Prefer injecting the full unread rewrite near the comment when possible
    comment = "// 获取未读消息数"
    if comment in content and "$unreadCount = ChatMessage::where('room_id'" in content:
        pattern = re.compile(
            r"[ \t]*// 获取未读消息数\n"
            r"[ \t]*\$unreadCount = ChatMessage::where\('room_id', \$userRoom->room_id\)\n"
            r"[ \t]*->where\('from_user', '<>', \$userID\)\n"
            r"[ \t]*->where\('created_at', '>', \$userRoom->joined_at\)\n"
            r"[ \t]*->count\(\);",
            re.M,
        )
        match = pattern.search(content)
        if match:
            indent = re.match(r"[ \t]*", match.group(0)).group(0)
            block = "\n".join(
                [
                    f"{indent}// 获取未读消息数",
                    f"{indent}$excludeSenderId = ($currentUser && isset($currentUser->id))",
                    f"{indent}    ? (int) $currentUser->id",
                    f"{indent}    : (int) (User::where('user_id', $userID)->value('id') ?: 0);",
                    f"{indent}$unreadQuery = ChatMessage::where('room_id', $userRoom->room_id)",
                    f"{indent}    ->where('sender_id', '<>', $excludeSenderId);",
                    f"{indent}if ($userRoom->joined_at) {{",
                    f"{indent}    $unreadQuery->where('created_at', '>', $userRoom->joined_at);",
                    f"{indent}}}",
                    f"{indent}$unreadCount = $unreadQuery->count();",
                ]
            )
            return content[: match.start()] + block + content[match.end() :]

    raise SystemExit(
        "Found from_user unread filter but could not safely rewrite the unread block; "
        "apply UNREAD_BLOCK_NEW manually."
    )


def patch_joined_at_format(content: str) -> str:
    """Fix all unsafe joined_at->format() calls (string timestamps break PHP)."""
    # getRoomMembers (and similar): "'joined_at' => $member->joined_at->format(...)"
    old_member = "'joined_at' => $member->joined_at->format('Y-m-d H:i:s'),"
    new_member = (
        "'joined_at' => $member->joined_at\n"
        "                    ? (is_object($member->joined_at)\n"
        "                        ? $member->joined_at->format('Y-m-d H:i:s')\n"
        "                        : (string) $member->joined_at)\n"
        "                    : null,"
    )
    if old_member in content:
        content = content.replace(old_member, new_member)

    # getUserRooms: "'joined_at'    => $userRoom->joined_at->format(...)"
    old_room = "'joined_at'    => $userRoom->joined_at->format('Y-m-d H:i:s'),"
    new_room = (
        "'joined_at'    => $userRoom->joined_at\n"
        "                    ? (is_object($userRoom->joined_at)\n"
        "                        ? $userRoom->joined_at->format('Y-m-d H:i:s')\n"
        "                        : (string) $userRoom->joined_at)\n"
        "                    : null,"
    )
    if old_room in content:
        content = content.replace(old_room, new_room)

    # Any remaining direct ->format on joined_at (defensive)
    pattern = re.compile(
        r"(['\"]joined_at['\"]\s*=>\s*)(\$[a-zA-Z_][\w\-]*>joined_at)->format\('Y-m-d H:i:s'\)"
    )

    def repl(m: re.Match[str]) -> str:
        prefix, expr = m.group(1), m.group(2)
        return (
            f"{prefix}{expr}\n"
            f"                    ? (is_object({expr})\n"
            f"                        ? {expr}->format('Y-m-d H:i:s')\n"
            f"                        : (string) {expr})\n"
            f"                    : null"
        )

    content = pattern.sub(repl, content)

    # Only flag direct unsafe calls (not those already guarded by is_object / is_string)
    unsafe = []
    for i, line in enumerate(content.splitlines(), 1):
        if "->joined_at->format(" not in line:
            continue
        # safe if this line is inside a ternary already rewritten
        stripped = line.strip()
        if stripped.startswith("? ") or "is_object(" in line or "is_string(" in line:
            continue
        # look at previous non-empty line for guard
        prev = ""
        for j in range(i - 2, max(-1, i - 6), -1):
            if content.splitlines()[j].strip():
                prev = content.splitlines()[j]
                break
        if "is_object(" in prev or "is_string(" in prev:
            continue
        unsafe.append((i, stripped))
    if unsafe:
        raise SystemExit(f"Still found unsafe joined_at->format(): {unsafe[:5]}")
    return content


def patch_member_role(content: str) -> str:
    for old, new in (
        ("'role'      => $member->role,", "'role'      => $member->role ?? 'member',"),
        ("'role' => $member->role,", "'role' => $member->role ?? 'member',"),
    ):
        if old in content:
            return content.replace(old, new)
    if "?? 'member'" in content:
        return content
    return content


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.is_file():
        sys.exit(f"File not found: {path}")

    original = path.read_text(encoding="utf-8")
    backup = path.with_suffix(path.suffix + f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
    shutil.copy2(path, backup)

    updated = original
    updated = patch_unread_block(updated)
    updated = patch_joined_at_format(updated)
    updated = patch_member_role(updated)

    if updated == original:
        print("No changes applied.")
        sys.exit(0)

    path.write_text(updated, encoding="utf-8")
    print(f"Patched: {path}")
    print(f"Backup:  {backup}")


if __name__ == "__main__":
    main()
