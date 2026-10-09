#!/usr/bin/env python3
"""
Remove UXIM data tied to attacker IP 103.179.45.220 (probes, malicious admins,
attack-window invite codes). Does not delete super_admin/master_admin accounts.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ATTACK_IP = "103.179.45.220"


def load_db(env_path: Path):
    text = env_path.read_text()
    def g(key: str) -> str:
        m = re.search(r"^" + key + r"\s*=\s*(.+)", text, re.M)
        return m.group(1).strip().strip('"') if m else ""

    return g("DB_HOST"), g("DB_USER"), g("DB_PASS"), g("DB_NAME")


def mysql_exec(host, user, password, db, sql: str) -> str:
    r = subprocess.run(
        ["mysql", "-h", host, "-u", user, f"-p{password}", db, "-e", sql],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout)
    return r.stdout


def main() -> int:
    env_path = Path(sys.argv[1] if len(sys.argv) > 1 else "/www/wwwroot/uxim/.env")
    host, user, pw, db = load_db(env_path)

    # Select malicious / probe accounts (never touch master_admin / super_admin rows).
    select_sql = f"""
SELECT id FROM users
WHERE role IN ('normal', 'admin')
  AND (
    last_login_ip = '{ATTACK_IP}'
    OR last_login_ip_current = '{ATTACK_IP}'
    OR username REGEXP '^(probe|pr7x|zz_i|zz_nonexist|zzzq267|i[0-9]+probe|i[0-9]+zwprobe)'
    OR username LIKE 'probe%'
    OR nickname LIKE '%probe%'
    OR nickname LIKE '%oast.me%'
    OR invite_code IN ('124', 'i1735376', 'zz'' OR ''1''=''1')
    OR (CHAR_LENGTH(TRIM(invite_code)) = 0 AND created_at >= '2026-09-21' AND created_at < '2026-09-23')
    OR id IN (101383, 101392, 101398, 101354, 101355, 101551)
  );
"""
    out = mysql_exec(host, user, pw, db, select_sql)
    ids = [line.strip() for line in out.splitlines() if line.strip().isdigit()]
    ids = sorted(set(ids), key=int)
    print(f"Users to purge: {len(ids)} -> {ids}")

    if not ids:
        print("No matching users.")
    else:
        id_list = ",".join(ids)
        purge = f"""
SET FOREIGN_KEY_CHECKS=0;
DELETE FROM user_login_devices WHERE user_id IN ({id_list});
DELETE FROM friends WHERE user_id IN ({id_list}) OR friend_id IN ({id_list});
DELETE FROM friend_requests WHERE from_user_id IN ({id_list}) OR to_user_id IN ({id_list});
DELETE FROM user_blocks WHERE user_id IN ({id_list}) OR blocked_user_id IN ({id_list});
DELETE FROM device_tokens WHERE user_id IN ({id_list});
DELETE FROM chat_room_members WHERE user_id IN ({id_list});
DELETE FROM user_chat_rooms WHERE user_id IN ({id_list});
DELETE FROM reports WHERE reporter_id IN ({id_list}) OR reported_user_id IN ({id_list});
DELETE FROM users WHERE id IN ({id_list});
SET FOREIGN_KEY_CHECKS=1;
"""
        mysql_exec(host, user, pw, db, purge)
        print("Purged user rows and direct relations.")

    # Invite codes minted during compromised admin sessions (attack window).
    invite_sql = """
DELETE FROM invite_codes
WHERE created_at >= '2026-09-21 14:50:00'
  AND created_at < '2026-09-22 09:00:00'
  AND created_by IN (2, 100048, 100209, 100412, 100832, 100049, 100075);
"""
    mysql_exec(host, user, pw, db, invite_sql)
    print("Removed attack-window invite codes from compromised admins.")

    # Clear attacker IP markers on retained admin accounts.
    clear_sql = f"""
UPDATE users
SET last_login_ip_current = NULL,
    last_login_region_current = NULL
WHERE last_login_ip_current = '{ATTACK_IP}'
  AND role IN ('super_admin', 'master_admin', 'admin');
"""
    mysql_exec(host, user, pw, db, clear_sql)
    print("Cleared last_login IP fields on surviving admin accounts.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
