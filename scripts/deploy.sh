#!/bin/bash
set -e

DOMAIN="${DOMAIN:-localhost}"
ENV="${DJANGO_ENV:-production}"

echo "============================================"
echo " Trust Management System - Deployment"
echo " Domain: $DOMAIN"
echo " Environment: $ENV"
echo "============================================"
echo ""

# Pre-flight checks
echo "[1/6] Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "ERROR: docker compose is required"; exit 1; }

if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Check required env vars
source .env
if [ "$DJANGO_SECRET_KEY" = "your-secret-key-here-change-in-production" ] || [ -z "$DJANGO_SECRET_KEY" ]; then
    echo "ERROR: DJANGO_SECRET_KEY must be set to a unique value"
    echo "Generate one: python -c \"import secrets; print(secrets.token_urlsafe(50))\""
    exit 1
fi

# Setup SSL
echo "[2/6] Setting up SSL certificates..."
if [ ! -f nginx/ssl/fullchain.pem ]; then
    DOMAIN="$DOMAIN" CERTBOT_EMAIL="${CERTBOT_EMAIL:-}" ./scripts/setup-ssl.sh
else
    echo "SSL certificates already exist. Skipping."
fi

# Build images
echo "[3/6] Building Docker images..."
docker compose build

# Start infrastructure (db + redis)
echo "[4/6] Starting infrastructure..."
docker compose up -d postgres redis
echo "Waiting for services to be healthy..."
sleep 5

# Start application
echo "[5/6] Starting application..."
docker compose up -d web websocket

# Wait for app health
echo "Waiting for application health check..."
for i in $(seq 1 30); do
    if docker compose exec web python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live/')" 2>/dev/null; then
        echo "Application is healthy!"
        break
    fi
    sleep 2
done

# Start nginx
echo "[6/6] Starting Nginx..."
docker compose up -d nginx certbot

echo ""
echo "============================================"
echo " Deployment complete!"
echo ""
echo " HTTP:  http://$DOMAIN  (redirects to HTTPS)"
echo " HTTPS: https://$DOMAIN"
echo " Health: https://$DOMAIN/health/"
echo ""
echo " Useful commands:"
echo "   docker compose logs -f         # View logs"
echo "   docker compose ps              # Service status"
echo "   docker compose exec web bash   # Shell into app"
echo "   make security-audit            # Run security check"
echo "============================================"
