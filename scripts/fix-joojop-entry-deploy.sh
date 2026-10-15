#!/usr/bin/env bash
# 在入口机 207.56.20.191 上执行（需 root SSH）。修复公网 api.joojop.com 仍返回 v12 与 /health 404。
# 副本与源站 /www/wwwroot/scripts/fix-joojop-entry-deploy.sh 保持同步。
set -euo pipefail
ORIGIN_IP="202.95.14.138"
ORIGIN_HOST="api.tyyjeb.cn"
SITE_ROOT="/www/wwwroot/api.joojop.com"
EXT_DIR="/www/server/panel/vhost/nginx/extension/api.joojop.com"
PROXY_CONF="$EXT_DIR/feibao_proxy.conf"

mkdir -p "$SITE_ROOT" "$EXT_DIR"
SRC="/www/wwwroot/scripts/joojop-config-v20.json"
python3 -c "import json; json.load(open('${SRC}'))"
cp -f "${SRC}" "${SITE_ROOT}/config.json"

# 写入 extension（由 vhost 内 include extension/api.joojop.com/*.conf 加载，勿在 server 块外 include）
cat > "$PROXY_CONF" <<NGX
location ^~ /ws {
    proxy_pass http://${ORIGIN_IP}/ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host ${ORIGIN_HOST};
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_buffering off;
    proxy_request_buffering off;
    proxy_read_timeout 3600s;
    proxy_send_timeout 30s;
    proxy_max_temp_file_size 0;
    gzip off;
    tcp_nodelay on;
}
location ^~ /auth/ {
    proxy_pass http://${ORIGIN_IP}/auth/;
    proxy_set_header Host ${ORIGIN_HOST};
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    client_max_body_size 50m;
}
location ^~ /login {
    proxy_pass http://${ORIGIN_IP}/login;
    proxy_set_header Host ${ORIGIN_HOST};
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
}
location = /health {
    proxy_pass http://${ORIGIN_IP}/health;
    proxy_set_header Host ${ORIGIN_HOST};
}
NGX

# 清理历史上误追加在 server 块外的 include
CONF="/www/server/panel/vhost/nginx/api.joojop.com.conf"
sed -i 's/}include \/www\/server\/panel\/vhost\/nginx\/extension\/api.joojop.com\/feibao_proxy.conf;/}/' "$CONF" 2>/dev/null || true

/www/server/nginx/sbin/nginx -t
/www/server/nginx/sbin/nginx -s reload
echo "OK: entry config.json=v20 (static); proxy ws/auth/login/health -> ${ORIGIN_IP} Host ${ORIGIN_HOST}"
