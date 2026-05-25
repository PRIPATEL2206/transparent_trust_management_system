#!/bin/bash
set -e

echo "=== Trust Management System - Production Entrypoint ==="

# Wait for database
echo "[1/5] Waiting for database..."
python manage.py wait_for_db --timeout 30

# Run migrations
echo "[2/5] Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "[3/5] Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || python manage.py collectstatic --noinput

# Run preflight checks
echo "[4/5] Running preflight checks..."
python manage.py preflight || true

# Start application
echo "[5/5] Starting application server..."
exec gunicorn a_core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --config gunicorn.conf.py
