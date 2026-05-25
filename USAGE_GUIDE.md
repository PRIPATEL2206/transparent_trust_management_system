# Trust Management System — Usage & Testing Guide

A complete guide to set up, run, and test every feature of the Trust Management System locally and in production.

---

## Table of Contents

1. [Local Development Setup](#1-local-development-setup)
2. [Production Deployment](#2-production-deployment)
3. [User Accounts & Roles](#3-user-accounts--roles)
4. [Feature Testing Walkthrough (UI)](#4-feature-testing-walkthrough-ui)
5. [API & Endpoint Reference](#5-api--endpoint-reference)
6. [Automated Testing](#6-automated-testing)
7. [Load Testing](#7-load-testing)
8. [Monitoring & Observability](#8-monitoring--observability)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Local Development Setup

### Prerequisites

- Python 3.12+
- Git
- Docker & Docker Compose (optional, for PostgreSQL/Redis)
- A modern browser (Chrome/Firefox)

### Quick Start (SQLite — Simplest)

```bash
# Clone and enter project
cd trust-management-django

# Create virtual environment
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env: set DJANGO_ENV=development

# Run setup (creates admin user, seeds roles, collects static)
python manage.py makemigrations
python manage.py migrate
python manage.py setup_project --create-admin
python manage.py collectstatic --noinput

# Seed test data for manual testing
python manage.py seed_test_data

# Start development server
python manage.py runserver
```

Open http://localhost:8000 in your browser.

### With PostgreSQL + Redis (Recommended)

```bash
# Start database services
make db-up
# or: docker compose -f docker-compose.dev.yml up -d

# Wait for database to be ready
make db-wait

# Set environment variables in .env:
#   DJANGO_ENV=development
#   DB_ENGINE=django.db.backends.postgresql
#   DB_NAME=trust_management
#   DB_USER=postgres
#   DB_PASSWORD=devpass
#   DB_HOST=localhost
#   DB_PORT=5432
#   REDIS_URL=redis://localhost:6379/0
#   CACHE_BACKEND=django.core.cache.backends.redis.RedisCache

# Run setup
python manage.py makemigrations
python manage.py migrate
python manage.py setup_project --create-admin
python manage.py seed_test_data

# Start server
python manage.py runserver
```

### For WebSocket Chat Testing (ASGI)

```bash
# Use Daphne instead of runserver
make run-asgi
# or: daphne a_core.asgi:application --bind 0.0.0.0 --port 8000
```

### Verify Setup

```bash
# Run preflight checks
make preflight

# Run security audit
make security-audit

# Run smoke tests
bash scripts/smoke-test.sh http://localhost:8000
```

---

## 2. Production Deployment

### Full Docker Stack

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with production values:
#   DJANGO_ENV=production
#   DJANGO_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(50))">
#   DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
#   DB_PASSWORD=<strong-password>
#   REDIS_URL=redis://redis:6379/0

# 2. Deploy (builds, starts services, sets up SSL)
make deploy
# or: bash scripts/deploy.sh

# 3. Verify deployment
make smoke-test-prod
# or: bash scripts/smoke-test.sh https://yourdomain.com

# 4. Start monitoring (optional)
make monitoring-up
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### Production Architecture

```
Internet → Nginx (SSL, rate limit) → Django (Gunicorn) → PostgreSQL
                                   → Daphne (WebSocket)  → Redis (cache/channels)
```

### Production Checklist

- [ ] `DJANGO_SECRET_KEY` set to unique random value
- [ ] `DJANGO_ALLOWED_HOSTS` set to actual domain(s)
- [ ] `DJANGO_DEBUG=False`
- [ ] PostgreSQL configured (not SQLite)
- [ ] Redis configured for cache + channels
- [ ] SSL certificate installed
- [ ] Email SMTP configured
- [ ] `SENTRY_DSN` set for error tracking
- [ ] `METRICS_API_KEY` set for metrics endpoint
- [ ] Backup schedule configured
- [ ] Health check monitoring configured

---

## 3. User Accounts & Roles

### Default Accounts (after `setup_project --create-admin`)

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `admin` | `admin123` | super_admin | Full system access |

### Test Accounts (after `seed_test_data`)

| Username | Password | Role | Purpose |
|----------|----------|------|---------|
| `admin` | `admin123` | super_admin | Manage everything |
| `manager1` | `Test@12345` | admin | Approve donations/expenses, manage users |
| `member1` | `Test@12345` | member | Create donations, expenses, chat |
| `member2` | `Test@12345` | member | Second member for chat/approvals |
| `user1` | `Test@12345` | user | Basic access, browse products |
| `ngo_org1` | `Test@12345` | ngo | Submit fund requests |

### Role Permissions

| Role | Can Do |
|------|--------|
| **super_admin** | Everything + site config + role management |
| **admin** | Approve content, manage users, view dashboard, export data |
| **member** | Create donations/expenses, chat, order products |
| **user** | View public content, browse products, view notices |
| **ngo** | Submit fund requests, view approved funding |

---

## 4. Feature Testing Walkthrough (UI)

### 4.1 Authentication & Security

#### Register a New User
1. Go to http://localhost:8000/auth/register/
2. Fill in: username, email, password (min 10 chars, mixed case + number + special)
3. Click "Register"
4. **Expected**: Redirected to home, yellow banner shows "Verify your email"
5. Check console output (development) for verification email
6. Click verification link or go to http://localhost:8000/auth/verify-email/resend/

#### Login
1. Go to http://localhost:8000/auth/login/
2. Enter credentials
3. **Expected**: Redirected to home page with "Login successful" message

#### Test Rate Limiting
1. Try 5 wrong passwords on login
2. **Expected**: "Account temporarily locked" message after 5 failures
3. Wait 5 minutes or clear cache

#### Two-Factor Authentication (Admin)
1. Login as `admin`
2. Go to http://localhost:8000/auth/settings/
3. Click "Enable 2FA" in the 2FA section
4. Scan QR code with authenticator app (Google Authenticator, Authy)
5. Enter 6-digit code and confirm
6. **Expected**: Backup codes shown — save these!
7. Logout and login again
8. **Expected**: 2FA verification screen appears after password

#### Password Change
1. Go to http://localhost:8000/auth/settings/
2. Enter old password and new password (twice)
3. **Expected**: "Password changed successfully" — other sessions flushed

#### Profile Update
1. Go to http://localhost:8000/auth/profile/
2. Update name, email, avatar
3. **Expected**: Changes saved, profile displayed

---

### 4.2 Roles & Permissions

#### View Roles (Admin)
1. Login as `admin`
2. Go to http://localhost:8000/roles/
3. **Expected**: List of all users with their roles

#### Assign Role
1. As `admin`, go to /roles/
2. Click "Assign" next to a user
3. Select new role → Submit
4. **Expected**: Role updated immediately

#### Role Request (Member)
1. Login as `member1`
2. Go to http://localhost:8000/roles/request/
3. Request "admin" role with justification
4. **Expected**: "Request submitted" message

#### Approve Role Request (Admin)
1. Login as `admin`
2. Go to http://localhost:8000/roles/pending/
3. Click Approve/Reject on pending request
4. **Expected**: Role request actioned, user notified

---

### 4.3 Donations

#### Add Donation
1. Login as `member1`
2. Go to http://localhost:8000/donation/add-donation/
3. Fill in: donor name, amount, type, description
4. Submit
5. **Expected**: Donation created with "pending" approval status

#### Manage Donations (Admin)
1. Login as `admin` or `manager1`
2. Go to http://localhost:8000/donation/donations/admin/
3. See all donations with status filters
4. Click Approve/Reject on pending donations
5. **Expected**: Status updated, appears in transparency page

#### Export Donations
1. As admin, go to /donation/donations/admin/export/?format=csv
2. **Expected**: CSV file downloads with all donation data

---

### 4.4 Expenses

#### Create Expense
1. Login as `member1`
2. Go to http://localhost:8000/expenses/create/
3. Fill in: title, amount, category, description, attach receipt (optional)
4. Submit
5. **Expected**: Expense created as "draft"

#### Submit for Approval
1. Go to http://localhost:8000/expenses/
2. Click "Submit" on a draft expense
3. **Expected**: Status changes to "pending"

#### Approve Expense (Admin)
1. Login as `admin`
2. Go to http://localhost:8000/expenses/admin/
3. Filter by "pending"
4. Click Approve → status becomes "approved"
5. Click "Mark Paid" → status becomes "paid"

#### Export Expenses
1. As admin, go to /expenses/admin/export/?format=csv
2. **Expected**: CSV file downloads

---

### 4.5 Payments & Receipts

#### Make a Payment
1. Login as `member1`
2. Go to http://localhost:8000/payments/
3. Select payment type (membership/fee), enter amount
4. Submit
5. **Expected**: Transaction created, receipt auto-generated

#### View Payment History
1. Go to http://localhost:8000/payments/history/
2. **Expected**: List of all your transactions

#### Download Receipt
1. In payment history, click "Download Receipt"
2. **Expected**: PDF receipt downloads (generated by WeasyPrint)

---

### 4.6 Notices & Notifications

#### Create Notice
1. Login as `member1` or `admin`
2. Go to http://localhost:8000/notices/create/
3. Fill in: title, content, priority, expiry date
4. Submit
5. **Expected**: Notice created (pending approval if not admin)

#### Approve Notice (Admin)
1. Login as `admin`
2. Go to http://localhost:8000/notices/admin/
3. Approve pending notices
4. **Expected**: Notice appears on public notice board

#### View Notifications
1. Click bell icon in navbar (shows unread count)
2. Go to http://localhost:8000/notices/notifications/
3. Click "Mark as Read" or "Mark All Read"

---

### 4.7 Products & Orders

#### Browse Products
1. Go to http://localhost:8000/products/
2. **Expected**: Grid of active products with prices/discounts

#### Place Order
1. Click on a product → View details
2. Click "Order" → Select quantity
3. Submit
4. **Expected**: Order placed, status "pending"

#### Manage Products (Admin)
1. Login as `admin`
2. Go to http://localhost:8000/products/admin/products/
3. Create/edit products (name, price, stock, discount, category)

#### Manage Orders (Admin)
1. Go to http://localhost:8000/products/admin/orders/
2. Confirm/process/deliver orders

---

### 4.8 NGO Fund Requests

#### Submit Fund Request (NGO)
1. Login as `ngo_org1`
2. Go to http://localhost:8000/ngo/create/
3. Fill in: title, description, amount requested, supporting documents
4. Submit
5. **Expected**: Request created as "pending"

#### Review Fund Requests (Admin)
1. Login as `admin`
2. Go to http://localhost:8000/ngo/admin/
3. Review request, set approved amount
4. Approve/Reject
5. **Expected**: NGO user notified of decision

---

### 4.9 Chat (WebSocket)

> **Requires**: ASGI server (Daphne) — run `make run-asgi`

#### Create Chat Group
1. Login as `member1`
2. Go to http://localhost:8000/chat/
3. Click "Create Group"
4. Name the group, add members
5. **Expected**: Group created

#### Send Messages
1. Open a chat group
2. Type message and send
3. **Open a second browser** logged in as `member2`
4. Open the same group
5. **Expected**: Messages appear in real-time (WebSocket)

#### Manage Members
1. As group creator, click "Manage Members"
2. Add/remove members
3. **Expected**: Members list updated

---

### 4.10 Dashboard & Reports (Admin)

#### View Dashboard
1. Login as `admin`
2. Go to http://localhost:8000/dashboard/
3. **Expected**: Charts showing donations, expenses, user stats, money flow

#### View Activity Log
1. Go to http://localhost:8000/dashboard/activity/
2. **Expected**: Chronological list of all system actions

#### Generate Report
1. Go to http://localhost:8000/reports/
2. Select report type (donations/expenses/transactions/members)
3. Set date range, format (CSV or PDF)
4. Click "Generate"
5. **Expected**: Report generated, download link appears

---

### 4.11 Transparency (Public)

1. Go to http://localhost:8000/transparency/ (no login required)
2. **Expected**: Aggregated financial data — donations received, expenses, fund allocation
3. No personal information (PII) visible

---

### 4.12 Site Configuration (Super Admin)

1. Login as `admin` (super_admin role)
2. Go to http://localhost:8000/config/
3. Edit: Trust name, contact info, membership fees, meta tags
4. Save
5. **Expected**: Changes reflected site-wide (header, footer, SEO meta)

---

### 4.13 Approval Engine

1. Login as `admin`
2. Go to http://localhost:8000/approvals/
3. **Expected**: All pending approvals across the system (donations, notices, expenses, NGO requests)
4. Approve/Reject with notes
5. **Expected**: Original item status updated, requester notified

---

## 5. API & Endpoint Reference

### Health & System

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/health/` | Optional API key | Full health check (DB + cache + disk) |
| GET | `/health/live/` | None | Liveness probe (process alive) |
| GET | `/health/ready/` | None | Readiness probe (DB + cache OK) |
| GET | `/metrics/` | Optional Bearer token | Prometheus metrics |
| GET | `/robots.txt` | None | SEO robots |
| GET | `/sitemap.xml` | None | XML sitemap |
| GET | `/.well-known/security.txt` | None | Security contact |

### Authentication

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/auth/login/` | Login |
| GET/POST | `/auth/register/` | Register |
| POST | `/auth/logout/` | Logout |
| GET/POST | `/auth/profile/` | View/edit profile |
| GET/POST | `/auth/settings/` | Password change, 2FA, deactivate |
| GET | `/auth/verify-email/<token>/` | Verify email |
| POST | `/auth/verify-email/resend/` | Resend verification |
| GET/POST | `/auth/2fa/setup/` | Setup 2FA |
| POST | `/auth/2fa/confirm/` | Confirm 2FA |
| GET/POST | `/auth/2fa/verify/` | Verify 2FA on login |
| POST | `/auth/2fa/disable/` | Disable 2FA |
| GET | `/auth/export-data/` | Export personal data |

### Donations

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET/POST | `/donation/add-donation/` | Member+ | Add donation |
| GET/POST | `/donation/add-donation-types/` | Admin | Add donation types |
| GET | `/donation/donation/` | Any | View donation types |
| GET | `/donation/donations/admin/` | Admin | Manage donations |
| GET | `/donation/donations/admin/export/` | Admin | Export CSV/PDF |
| POST | `/donation/donations/<id>/action/` | Admin | Approve/reject |

### Expenses

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/expenses/` | Member+ | My expenses |
| GET/POST | `/expenses/create/` | Member+ | Create expense |
| POST | `/expenses/<id>/submit/` | Owner | Submit for approval |
| GET | `/expenses/admin/` | Admin | All expenses |
| GET | `/expenses/admin/export/` | Admin | Export report |
| POST | `/expenses/<id>/action/` | Admin | Approve/reject/pay |

### Payments

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET/POST | `/payments/` | Member+ | Make payment |
| GET | `/payments/history/` | Any auth | Payment history |
| GET | `/payments/receipt/<id>/` | Owner/Admin | Download receipt PDF |
| GET | `/payments/admin/` | Admin | All payments |

### Notices

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/notices/` | Public | Active notices |
| GET/POST | `/notices/create/` | Member+ | Create notice |
| GET | `/notices/admin/` | Admin | Manage notices |
| POST | `/notices/<id>/approve/` | Admin | Approve notice |
| GET | `/notices/notifications/` | Auth | My notifications |
| POST | `/notices/notifications/mark-read/<id>/` | Auth | Mark read |
| POST | `/notices/notifications/mark-all-read/` | Auth | Mark all read |

### Products

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/products/` | Public | Product catalog |
| GET | `/products/<id>/` | Public | Product detail |
| POST | `/products/<id>/order/` | Auth | Place order |
| GET | `/products/orders/` | Auth | My orders |
| POST | `/products/orders/<id>/cancel/` | Owner | Cancel order |
| POST | `/products/admin/products/create/` | Admin | Create product |
| GET | `/products/admin/orders/` | Admin | Manage orders |

### NGO Requests

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/ngo/` | NGO/Admin | Fund requests |
| GET/POST | `/ngo/create/` | NGO | New request |
| GET | `/ngo/admin/` | Admin | Manage requests |
| POST | `/ngo/<id>/action/` | Admin | Approve/reject |

### Chat

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/chat/` | Auth | Chat groups |
| GET/POST | `/chat/create/` | Auth | Create group |
| GET | `/chat/<id>/` | Member | Chat room (WebSocket) |
| POST | `/chat/<id>/members/` | Creator | Manage members |

### Dashboard & Reports

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/dashboard/` | Admin | Analytics dashboard |
| GET | `/dashboard/activity/` | Admin | Activity log |
| GET/POST | `/reports/` | Admin | Generate reports |
| GET | `/reports/<id>/download/` | Admin | Download report |
| GET | `/transparency/` | Public | Public transparency |

---

## 6. Automated Testing

### Run All Tests

```bash
# Quick run
make test

# With coverage
make test-cov

# Verbose output
make test-verbose

# Stop on first failure
make test-fast

# Run specific test file
pytest tests/test_payments.py -v

# Run specific test
pytest tests/test_payments.py::TestPaymentService::test_initiate_payment -v
```

### Test Categories

```bash
# Unit tests (fast, no DB)
pytest -m "not integration and not slow"

# Integration tests (requires services)
pytest -m integration

# Security tests
pytest a_customeauth/test_security.py -v

# Specific module tests
pytest tests/test_cors.py -v
pytest tests/test_password_age.py -v
pytest tests/test_file_validation.py -v
pytest tests/test_exports_integration.py -v
```

### Run the Full E2E Test Suite

```bash
# Seed test data first
python manage.py seed_test_data

# Run end-to-end tests
pytest tests/test_e2e_full_system.py -v
```

### Test Coverage Report

```bash
make test-cov
# Opens HTML report showing which lines are covered
# Minimum threshold: 60%
```

---

## 7. Load Testing

### Setup

```bash
# Create load test users
make loadtest-seed

# Start the server (in another terminal)
make run
```

### Interactive Mode (Web UI)

```bash
make loadtest
# Open http://localhost:8089
# Set users: 50, spawn rate: 5
# Click "Start"
# Watch real-time charts
```

### Headless Mode (CI)

```bash
# Standard (50 users, 60 seconds)
make loadtest-headless

# Stress test (200 users, 120 seconds)
make loadtest-stress
```

### Distributed Mode (Docker)

```bash
# Ensure main app is running via docker compose
make docker-up

# Start Locust cluster (1 master + 4 workers)
docker compose -f docker-compose.loadtest.yml up
# Open http://localhost:8089
```

### Performance Thresholds

The load test runner enforces these limits:

| Metric | Threshold |
|--------|-----------|
| p95 response time | < 800ms |
| p99 response time | < 2000ms |
| Max response time | < 5000ms |
| Failure rate | < 1% |
| Throughput | > 10 req/s |

If any threshold is breached, the runner exits with code 1.

### Cleanup

```bash
make loadtest-cleanup
```

---

## 8. Monitoring & Observability

### Start Monitoring Stack

```bash
make monitoring-up
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | — |
| App Metrics | http://localhost:8000/metrics/ | Bearer token (if METRICS_API_KEY set) |

### Grafana Dashboard

The pre-configured dashboard shows:
- Request rate (req/s)
- Error rate (4xx/5xx)
- Average response time
- Active requests gauge
- Login success/failure rates
- Business metrics (donations, expenses, payments)

### Audit Logs

Security events are logged to `logs/audit.log`:

```bash
# View recent audit events
tail -50 logs/audit.log | python -m json.tool

# Search for login failures
grep "login_attempt" logs/audit.log

# Search for role changes
grep "role_change" logs/audit.log
```

### Application Logs

```bash
# View application logs
tail -f logs/app.log

# Pretty-print JSON logs
tail -f logs/app.log | python -m json.tool
```

### Sentry (Error Tracking)

If `SENTRY_DSN` is set, unhandled exceptions and performance traces are sent to Sentry automatically. Smart sampling:
- Health endpoints: 0% (no noise)
- API endpoints: 30%
- General pages: 10%

---

## 9. Troubleshooting

### Common Issues

#### "No module named 'services'"
```bash
# Ensure you're in the project root directory
cd trust-management-django
python manage.py runserver
```

#### Database migration errors
```bash
# Reset migrations if conflicts
python manage.py makemigrations
python manage.py migrate

# Nuclear option (dev only): delete db.sqlite3 and re-migrate
rm db.sqlite3
python manage.py migrate
python manage.py setup_project --create-admin
```

#### Redis connection refused
```bash
# Start Redis
make db-up
# or use LocMem cache in .env:
# CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache
```

#### WebSocket chat not working
```bash
# Must use ASGI server, not runserver
make run-asgi
# Ensure CHANNEL_BACKEND is set (InMemoryChannelLayer for dev, Redis for prod)
```

#### Static files not loading
```bash
python manage.py collectstatic --noinput
# Check that whitenoise middleware is in MIDDLEWARE list
```

#### Email verification not sending
```bash
# In development, emails print to console
# Check terminal output after registration
# For testing: set EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

#### 2FA QR code not showing
```bash
# Ensure qrcode package is installed
pip install qrcode==8.0
```

#### Permission denied errors
```bash
# Check your role
python manage.py shell -c "from roles.services import RoleService; from django.contrib.auth.models import User; u=User.objects.get(username='your_username'); print(RoleService.get_user_role(u))"
```

### Useful Commands

```bash
# Check system health
python manage.py preflight

# Security audit
python manage.py security_audit --strict

# Clean up old data
python manage.py cleanup_data --days 90 --dry-run

# Backup database
python manage.py backup_db

# Django shell (inspect data)
python manage.py shell

# Create superuser manually
python manage.py createsuperuser
```

---

## Quick Reference Card

```
LOCAL DEV:
  make setup          → Install + migrate + create admin
  make run            → Start server on :8000
  make test           → Run test suite
  make preflight      → Verify config

PRODUCTION:
  make deploy         → Full Docker deployment
  make smoke-test-prod → Post-deploy verification
  make monitoring-up  → Start Prometheus + Grafana
  make security-audit → Check security config

TESTING:
  make test-cov       → Tests with coverage
  make loadtest       → Load test web UI
  make loadtest-headless → CI-mode load test

MAINTENANCE:
  make backup         → Backup database
  make cleanup        → Remove old data (90d)
  make db-reset       → Fresh database
```
