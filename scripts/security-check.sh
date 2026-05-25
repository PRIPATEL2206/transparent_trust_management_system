#!/bin/bash
set -e

echo "=== Production Security Hardening Checklist ==="
echo ""

PASS=0
FAIL=0

check() {
    local desc="$1"
    local result="$2"
    if [ "$result" = "ok" ]; then
        echo "  [PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $desc"
        FAIL=$((FAIL + 1))
    fi
}

# .env checks
echo "--- Environment ---"
if [ -f .env ]; then
    source .env
    if [ "$DJANGO_DEBUG" = "False" ] || [ "$DJANGO_DEBUG" = "false" ]; then
        check "DEBUG is disabled" "ok"
    else
        check "DEBUG is disabled" "fail"
    fi

    if [ "$DJANGO_SECRET_KEY" != "your-secret-key-here-change-in-production" ] && [ -n "$DJANGO_SECRET_KEY" ]; then
        check "SECRET_KEY is set and not default" "ok"
    else
        check "SECRET_KEY is set and not default" "fail"
    fi

    if [ "$DJANGO_ALLOWED_HOSTS" != "*" ] && [ -n "$DJANGO_ALLOWED_HOSTS" ]; then
        check "ALLOWED_HOSTS is restricted" "ok"
    else
        check "ALLOWED_HOSTS is restricted" "fail"
    fi

    if [ -n "$POSTGRES_PASSWORD" ] && [ "$POSTGRES_PASSWORD" != "trustpass" ]; then
        check "Database password is not default" "ok"
    else
        check "Database password is not default" "fail"
    fi
else
    echo "  [FAIL] .env file not found"
    FAIL=$((FAIL + 4))
fi

# SSL checks
echo ""
echo "--- SSL/TLS ---"
if [ -f nginx/ssl/fullchain.pem ]; then
    check "SSL certificate exists" "ok"
    EXPIRY=$(openssl x509 -enddate -noout -in nginx/ssl/fullchain.pem 2>/dev/null | cut -d= -f2)
    if [ -n "$EXPIRY" ]; then
        echo "       Certificate expires: $EXPIRY"
    fi
else
    check "SSL certificate exists" "fail"
fi

if [ -f nginx/ssl/privkey.pem ]; then
    PERMS=$(stat -c %a nginx/ssl/privkey.pem 2>/dev/null || stat -f %OLp nginx/ssl/privkey.pem 2>/dev/null)
    if [ "$PERMS" = "600" ] || [ "$PERMS" = "640" ]; then
        check "Private key permissions restricted" "ok"
    else
        check "Private key permissions restricted (current: $PERMS)" "fail"
    fi
else
    check "Private key exists" "fail"
fi

# Docker checks
echo ""
echo "--- Docker ---"
if docker compose ps --format json 2>/dev/null | grep -q "running"; then
    check "Containers are running" "ok"
else
    check "Containers are running" "fail"
fi

# File permission checks
echo ""
echo "--- File Permissions ---"
if [ ! -r .env ] || [ "$(stat -c %a .env 2>/dev/null || echo 644)" = "600" ]; then
    check ".env is not world-readable" "ok"
else
    check ".env is not world-readable (chmod 600 .env)" "fail"
fi

if [ -f db.sqlite3 ]; then
    check "SQLite database not present in production" "fail"
else
    check "No SQLite database file" "ok"
fi

# Summary
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ $FAIL -gt 0 ]; then
    echo "FIX the above issues before going live."
    exit 1
else
    echo "All checks passed. Ready for production."
fi
