#!/usr/bin/env bash
# 星语扫描封禁策略安装/回滚 — 需在 206.119.118.249 上以 root 执行
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HZ_BACKUP_ROOT="/www/wwwroot/HZ-backup"
TS="$(date +%Y%m%d-%H%M%S)"
BK="${HZ_BACKUP_ROOT}/HZ-backup-${TS}-scan-defense"

# 运维 SSH 白名单（空格分隔，可环境变量覆盖）
: "${HZ_SSH_ALLOW_IPS:=113.5.87.189}"

log() { echo "[HZ scan-defense] $*"; }

backup_mkdir() {
  mkdir -p "$BK"/{nginx,fail2ban,ufw,ssh}
  [[ -f /etc/nginx/conf.d/01-hz-anti-crawler-map.conf ]] && \
    cp -a /etc/nginx/conf.d/01-hz-anti-crawler-map.conf "$BK/nginx/" || true
  [[ -d /etc/fail2ban/jail.d ]] && cp -a /etc/fail2ban/jail.d "$BK/fail2ban/" || true
  ufw status numbered > "$BK/ufw/status-before.txt" 2>/dev/null || true
  cp -a /etc/ssh/sshd_config.d "$BK/ssh/" 2>/dev/null || true
  log "备份目录: $BK"
}

install_nginx() {
  cp "$PKG_ROOT/configs/nginx/01-hz-anti-crawler-map.conf" \
    /etc/nginx/conf.d/01-hz-anti-crawler-map.conf
  local snippet="/etc/nginx/snippets/hz-scan-drop.conf"
  mkdir -p /etc/nginx/snippets
  cp "$PKG_ROOT/configs/nginx/snippet-hz-scan-drop.conf" "$snippet"

  if ! grep -rq 'hz-scan-drop' /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null; then
    log "请在各 server{} 内加入: include /etc/nginx/snippets/hz-scan-drop.conf;"
    log "或执行: HZ_INJECT_NGINX=1 $0 install （将为 sites-enabled 批量注入，慎用）"
  fi

  if [[ "${HZ_INJECT_NGINX:-0}" == "1" ]]; then
    local n=0
    for f in /etc/nginx/sites-enabled/*.conf; do
      [[ -f "$f" ]] || continue
      grep -q 'hz-scan-drop' "$f" && continue
      sed -i '/server_name /a\    include /etc/nginx/snippets/hz-scan-drop.conf;' "$f"
      n=$((n + 1))
    done
    log "已向 $n 个 vhost 注入 scan-drop snippet"
  fi

  nginx -t
  systemctl reload nginx
  log "nginx 已 reload"
}

install_fail2ban() {
  cp "$PKG_ROOT/configs/fail2ban/filter.d/hz-nginx-crawler.conf" \
    /etc/fail2ban/filter.d/hz-nginx-crawler.conf

  local jail="/etc/fail2ban/jail.d/hz-scan-defense.local"
  cp "$PKG_ROOT/configs/fail2ban/jail.d/hz-scan-defense.local" "$jail"

  # 注入运维 IP 到 ignoreip
  local extra=""
  for ip in $HZ_SSH_ALLOW_IPS; do extra+=" $ip"; done
  sed -i "s/^ignoreip = .*/ignoreip = 127.0.0.1\/8 ::1 163.223.146.0\/24${extra}/" "$jail"

  fail2ban-client reload 2>/dev/null || systemctl restart fail2ban
  log "fail2ban 已 reload"
}

install_ssh_hardening() {
  cat > /etc/ssh/sshd_config.d/99-im-key-only.conf << 'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
PubkeyAuthentication yes
PermitRootLogin prohibit-password
UsePAM yes
EOF
  sshd -t
  systemctl reload sshd
  log "sshd 仅公钥"
}

install_ufw_ssh() {
  if ! command -v ufw >/dev/null; then
    log "未安装 ufw，跳过"
    return
  fi
  for ip in $HZ_SSH_ALLOW_IPS; do
    ufw allow from "$ip" to any port 17603 proto tcp comment "HZ-ssh-ops" || true
  done
  while ufw status numbered 2>/dev/null | grep -qE '17603/tcp.*ALLOW IN.*Anywhere'; do
    num=$(ufw status numbered | grep -E '17603/tcp.*ALLOW IN.*Anywhere' | head -1 | sed -n 's/^\[\([0-9]*\)\].*/\1/p')
    [[ -n "$num" ]] && ufw --force delete "$num" || break
  done
  ufw reload
  log "ufw 17603 已收紧为运维 IP"
}

cmd_install() {
  backup_mkdir
  install_nginx
  install_fail2ban
  install_ssh_hardening
  install_ufw_ssh
  log "安装完成。请执行验证清单（见 docs/异常扫描封禁策略.md）"
}

cmd_rollback() {
  local latest
  latest=$(ls -dt "${HZ_BACKUP_ROOT}"/HZ-backup-*-scan-defense 2>/dev/null | head -1)
  if [[ -z "$latest" ]]; then
    log "无 scan-defense 备份可回滚"
    exit 1
  fi
  [[ -f "$latest/nginx/01-hz-anti-crawler-map.conf" ]] && \
    cp -a "$latest/nginx/01-hz-anti-crawler-map.conf" /etc/nginx/conf.d/ || true
  [[ -d "$latest/fail2ban/jail.d" ]] && cp -a "$latest/fail2ban/jail.d/"* /etc/fail2ban/jail.d/ || true
  nginx -t && systemctl reload nginx
  fail2ban-client reload 2>/dev/null || true
  log "已从 $latest 回滚（ufw/ssh 请人工核对）"
}

case "${1:-install}" in
  install) cmd_install ;;
  rollback) cmd_rollback ;;
  *) echo "用法: $0 install|rollback"; exit 1 ;;
esac
