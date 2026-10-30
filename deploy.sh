#!/usr/bin/env bash
# Script deploy otomatis untuk VPS Ubuntu / Debian (24/7 Service)

set -e

echo "=================================================="
echo "    Deploying Umrah Footage AI on VPS (24/7)     "
echo "=================================================="

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "Docker belum terinstall. Menginstall Docker & Compose..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

echo "Membangun container dan menjalankan di background..."
docker compose down || true
docker compose build
docker compose up -d

echo ""
echo "=================================================="
echo " Aplikasi Umrah Footage AI Aktif 24/7!"
echo " Akses Web Dashboard di: http://<IP_VPS_ANDA>:8000"
echo " Monitoring Log: docker compose logs -f"
echo "=================================================="
