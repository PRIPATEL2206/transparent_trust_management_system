#!/bin/bash
set -e

DOMAIN="${DOMAIN:-localhost}"
EMAIL="${CERTBOT_EMAIL:-}"
STAGING="${CERTBOT_STAGING:-0}"

SSL_DIR="./nginx/ssl"
CERTBOT_DIR="./certbot"

echo "=== SSL Certificate Setup ==="
echo "Domain: $DOMAIN"

# Create directories
mkdir -p "$SSL_DIR" "$CERTBOT_DIR/www" "$CERTBOT_DIR/conf"

if [ "$DOMAIN" = "localhost" ] || [ "$DOMAIN" = "127.0.0.1" ]; then
    echo "Generating self-signed certificate for local development..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/privkey.pem" \
        -out "$SSL_DIR/fullchain.pem" \
        -subj "/C=US/ST=Local/L=Dev/O=TrustMgmt/CN=$DOMAIN" \
        2>/dev/null
    cp "$SSL_DIR/fullchain.pem" "$SSL_DIR/chain.pem"
    echo "Self-signed certificate created at $SSL_DIR/"
    echo "NOTE: Browsers will show a security warning. This is expected for local dev."
else
    if [ -z "$EMAIL" ]; then
        echo "ERROR: CERTBOT_EMAIL is required for Let's Encrypt"
        echo "Usage: DOMAIN=yourdomain.com CERTBOT_EMAIL=you@email.com ./scripts/setup-ssl.sh"
        exit 1
    fi

    STAGING_FLAG=""
    if [ "$STAGING" = "1" ]; then
        STAGING_FLAG="--staging"
        echo "Using Let's Encrypt STAGING (test certificates)"
    fi

    echo "Requesting Let's Encrypt certificate..."
    docker compose run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        $STAGING_FLAG \
        -d "$DOMAIN"

    # Copy certs to nginx ssl directory
    cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/fullchain.pem"
    cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/privkey.pem"
    cp "/etc/letsencrypt/live/$DOMAIN/chain.pem" "$SSL_DIR/chain.pem"

    echo "Let's Encrypt certificate installed for $DOMAIN"
    echo "Auto-renewal is handled by the certbot container."
fi

echo ""
echo "=== Done ==="
echo "Restart nginx: docker compose restart nginx"
