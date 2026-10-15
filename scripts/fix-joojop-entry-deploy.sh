#!/usr/bin/env bash
# 在入口机 207.56.20.191 上执行（需 root SSH）。修复公网 api.joojop.com 仍返回 v12 与 /health 404。
# 副本与源站 /www/wwwroot/scripts/fix-joojop-entry-deploy.sh 保持同步。
set -euo pipefail
ORIGIN_IP="202.95.14.138"
ORIGIN_HOST="api.yejhtf.com"
SITE_ROOT="/www/wwwroot/api.joojop.com"
CONF="/www/server/panel/vhost/nginx/api.joojop.com.conf"
EXT_DIR="/www/server/panel/vhost/nginx/extension/api.joojop.com"
PROXY_CONF="$EXT_DIR/feibao_proxy.conf"

mkdir -p "$SITE_ROOT" "$EXT_DIR"
SRC="/www/wwwroot/scripts/joojop-config-v20.json"
python3 -c "import json; json.load(open('${SRC}'))"
cp -f "${SRC}" "${SITE_ROOT}/config.json"

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
location = /health {
    proxy_pass http://${ORIGIN_IP}/health;
    proxy_set_header Host ${ORIGIN_HOST};
}
location = /config.json {
    proxy_pass http://${ORIGIN_IP}/config.json;
    proxy_set_header Host api.joojop.com;
    add_header Cache-Control "no-cache, no-store, must-revalidate" always;
}
NGX

if ! grep -q "feibao_proxy.conf" "$CONF" 2>/dev/null; then
  echo "include $PROXY_CONF;" >> "$CONF"
fi

/www/server/nginx/sbin/nginx -t
/www/server/nginx/sbin/nginx -s reload
echo "OK: entry proxies to origin; purge CDN /config.json in panel."
