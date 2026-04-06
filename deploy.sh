#!/bin/bash
# ================================================
# CSU Date 一键部署脚本 (Linux)
# 前后端都部署在同一台服务器
# 在服务器上执行: bash deploy.sh
# ================================================

set -e

APP_DIR="/opt/csudate"
DOMAIN="csudate.com"
BACKEND_DIR="$APP_DIR/csu-datedrop-backend"
FRONTEND_DIR="$APP_DIR/stitch"

echo ""
echo "========================================="
echo "  CSU Date Deploy"
echo "  Domain: $DOMAIN"
echo "========================================="
echo ""

# ── 1. 系统依赖 ──
echo "[1/7] install system dependencies..."
apt update -y
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx curl

# ── 2. Python 虚拟环境 ──
echo "[2/7] setup Python venv..."
cd "$BACKEND_DIR"
python3.11 -m venv venv
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt -q
echo "  Python deps installed"

# ── 3. 初始化数据库 ──
echo "[3/7] init database..."
cd "$BACKEND_DIR"
./venv/bin/python3.11 -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine); print('  DB ready')"

# ── 4. systemd 后端服务 ──
echo "[4/7] configure backend service..."
cat > /etc/systemd/system/csudate.service << SERVICEEOF
[Unit]
Description=CSU Date Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BACKEND_DIR
EnvironmentFile=$BACKEND_DIR/.env
Environment=PATH=$BACKEND_DIR/venv/bin:/usr/bin
ExecStart=$BACKEND_DIR/venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8888
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable csudate
systemctl restart csudate
sleep 2

if curl -sf http://127.0.0.1:8888/api/stats > /dev/null 2>&1; then
    echo "  backend running OK"
else
    echo "  WARNING: backend may not be ready yet"
    journalctl -u csudate --no-pager -n 10
fi

# ── 5. Nginx 配置（前端静态 + API 反代）──
echo "[5/7] configure Nginx..."
cat > /etc/nginx/sites-available/csudate << NGINXEOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    root $FRONTEND_DIR;
    index index.html;

    # API reverse proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }

    # frontend fallback
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # static cache
    location ~* \.(png|jpg|jpeg|gif|ico|svg|css|js|woff2?)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    client_max_body_size 20m;
}
NGINXEOF

ln -sf /etc/nginx/sites-available/csudate /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
echo "  Nginx configured"

# ── 6. 防火墙 ──
echo "[6/7] configure firewall..."
if command -v ufw > /dev/null 2>&1; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    echo "  ufw configured"
else
    echo "  ufw not found, skip"
fi

# ── 7. SSL 证书 ──
echo "[7/7] request SSL certificate..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN \
    --non-interactive --agree-tos --email admin@csudate.com --redirect \
    && echo "  SSL OK" \
    || echo "  SSL failed. Make sure DNS points to this server first."

systemctl enable certbot.timer 2>/dev/null || true

# ── 验证 ──
echo ""
echo "========================================="
echo "  Deploy complete!"
echo ""
echo "  https://$DOMAIN"
echo ""
echo "  Useful commands:"
echo "    systemctl restart csudate   # restart backend"
echo "    journalctl -u csudate -f    # backend logs"
echo "    systemctl restart nginx     # restart nginx"
echo "    certbot renew               # renew SSL"
echo "========================================="
