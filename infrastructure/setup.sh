#!/bin/bash
# ============================================================================
# Chimera Runtime — EC2 Instance Setup Script
#
# Usage: Run as root on a fresh Ubuntu 22.04/24.04 EC2 instance
#   curl -sSL https://raw.githubusercontent.com/.../setup.sh | bash
#   OR: copy this to EC2 user data
# ============================================================================

set -euo pipefail

echo "============================================"
echo " Chimera Runtime — EC2 Setup"
echo "============================================"

# ── System Packages ──────────────────────────────────────────────
apt-get update -y
apt-get install -y \
    docker.io \
    docker-compose-plugin \
    git \
    sqlite3 \
    jq \
    curl

# Docker compose V2 alias
if ! command -v docker-compose &>/dev/null; then
    echo 'alias docker-compose="docker compose"' >> /root/.bashrc
fi

# Enable Docker
systemctl enable --now docker
usermod -aG docker ubuntu 2>/dev/null || true

# ── Install Caddy ────────────────────────────────────────────────
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg 2>/dev/null || true
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update -y
apt-get install -y caddy

# Stop default caddy (we'll configure our own)
systemctl stop caddy 2>/dev/null || true

# ── Clone Repository ─────────────────────────────────────────────
DEPLOY_DIR="/opt/chimera-runtime"
if [ ! -d "$DEPLOY_DIR" ]; then
    git clone https://github.com/your-org/chimera-runtime.git "$DEPLOY_DIR"
else
    cd "$DEPLOY_DIR" && git pull origin main
fi

# ── Create Directories ───────────────────────────────────────────
mkdir -p "$DEPLOY_DIR/audit_logs"
mkdir -p "$DEPLOY_DIR/data"

# ── Setup Caddyfile ──────────────────────────────────────────────
cp "$DEPLOY_DIR/infrastructure/Caddyfile" /etc/caddy/Caddyfile

# ── Start Caddy ──────────────────────────────────────────────────
systemctl enable caddy
systemctl start caddy

# ── Start Application ────────────────────────────────────────────
cd "$DEPLOY_DIR/dashboard"
docker compose -f docker-compose.yml -f docker-compose.aws.yml up -d --build

echo ""
echo "============================================"
echo " ✅ Chimera Runtime deployed!"
echo "    Frontend: https://runtime.chimera-protocol.com"
echo "    API:      https://api-runtime.chimera-protocol.com"
echo "============================================"
