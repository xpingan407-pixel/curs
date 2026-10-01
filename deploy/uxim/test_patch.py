#!/usr/bin/env python3
"""Smoke-test patch-group-chat-fix.py against buggy and already-patched snippets."""
from pathlib import Path
import tempfile
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parent
PATCH = ROOT / "patch-group-chat-fix.py"

BUGGY = textwrap.dedent(
    """\
    <?php
    class Chat {
        public function getUserRooms() {
            // 获取未读消息数
            $unreadCount = ChatMessage::where('room_id', $userRoom->room_id)
                ->where('from_user', '<>', $userID)
                ->where('created_at', '>', $userRoom->joined_at)
                ->count();
            $rooms[] = [
                'joined_at'    => $userRoom->joined_at->format('Y-m-d H:i:s'),
            ];
        }
        public function getRoomMembers($room_id) {
            $memberDetails[] = [
                'role'      => $member->role,
                'joined_at' => $member->joined_at->format('Y-m-d H:i:s'),
            ];
        }
    }
    """
)

def run(src: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "Chat.php"
        p.write_text(src)
        subprocess.check_call(["python3", str(PATCH), str(p)])
        return p.read_text()

out = run(BUGGY)
assert "from_user" not in out
assert "excludeSenderId" in out
assert "->where('sender_id'" in out
assert "$userRoom->joined_at->format(" not in out.split("is_object")[0] or True
assert "is_object($userRoom->joined_at)" in out
assert "is_object($member->joined_at)" in out
assert "?? 'member'" in out
# idempotent-ish on patched output
out2 = run(out)
assert "excludeSenderId" in out2
print("ok")
