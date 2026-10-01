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
    if UNREAD_BLOCK_OLD not in content:
        # minimal fallback: wrong column name only
        old = "->where('from_user', '<>', $userID)"
        if old not in content:
            raise SystemExit("Unread block not found (already patched or Chat.php changed).")
        return content.replace(old, "->where('sender_id', '<>', $excludeSenderId)")
    return content.replace(UNREAD_BLOCK_OLD, UNREAD_BLOCK_NEW)


def patch_joined_at_format(content: str) -> str:
    old = "'joined_at' => $member->joined_at->format('Y-m-d H:i:s'),"
    new = (
        "'joined_at' => $member->joined_at\n"
        "                    ? (is_object($member->joined_at)\n"
        "                        ? $member->joined_at->format('Y-m-d H:i:s')\n"
        "                        : (string) $member->joined_at)\n"
        "                    : null,"
    )
    if old not in content:
        if "is_object($member->joined_at)" in content:
            return content
        raise SystemExit("Could not find joined_at->format line in getRoomMembers.")
    return content.replace(old, new)


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
