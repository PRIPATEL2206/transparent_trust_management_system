# Trust Management System — Windows Setup & Testing Guide

Complete guide for setting up, running, and testing the entire system on Windows 10/11.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Database Options](#3-database-options)
4. [Running the Server](#4-running-the-server)
5. [Seed Test Data](#5-seed-test-data)
6. [Testing Every Feature (Step by Step)](#6-testing-every-feature)
7. [Running Automated Tests](#7-running-automated-tests)
8. [Docker on Windows](#8-docker-on-windows)
9. [Common Windows Issues & Fixes](#9-common-windows-issues--fixes)

---

## 1. Prerequisites

### Required Software

| Software | Version | Download |
|----------|---------|----------|
| Python | 3.12+ | https://www.python.org/downloads/ |
| Git | Latest | https://git-scm.com/download/win |
| VS Code (recommended) | Latest | https://code.visualstudio.com/ |

### Optional (for full features)

| Software | Purpose | Download |
|----------|---------|----------|
| Docker Desktop | PostgreSQL + Redis | https://www.docker.com/products/docker-desktop/ |
| Node.js | If rebuilding Tailwind CSS | https://nodejs.org/ |
| GTK3 Runtime | WeasyPrint PDF generation | https://github.com/nickvdyck/weasyprint-windows |

### Python Installation Notes (Windows)

1. Download Python 3.12+ from python.org
2. **CHECK** "Add Python to PATH" during installation
3. **CHECK** "Install pip"
4. Verify in PowerShell:
```powershell
python --version
# Python 3.12.x

pip --version
# pip 24.x
```

---

## 2. Installation

### Step 1: Clone the Project

```powershell
# Open PowerShell or Git Bash
cd C:\Users\YourName\Desktop\Projects
git clone <repository-url> trust-management-django
cd trust-management-django
```

### Step 2: Create Virtual Environment

```powershell
# PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# If you get "execution policy" error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1

# Git Bash alternative:
python -m venv venv
source venv/Scripts/activate
```

You should see `(venv)` prefix in your terminal.

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

**WeasyPrint Note (PDF generation):**
WeasyPrint requires GTK3 on Windows. If you get errors:
```powershell
# Option A: Install GTK3 (for PDF receipt generation)
# Download from: https://github.com/nickvdyck/weasyprint-windows
# Add GTK3 bin folder to PATH

# Option B: Skip WeasyPrint (PDFs won't generate, but everything else works)
# Comment out "weasyprint==62.3" in requirements.txt before pip install
```

### Step 4: Configure Environment

```powershell
# Copy example config
copy .env.example .env

# Open in editor
notepad .env
# OR
code .env
```

Edit `.env` with these minimal settings:
```ini
DJANGO_SECRET_KEY=my-dev-secret-key-change-in-production-12345
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_ENV=development
```

### Step 5: Run Database Setup

```powershell
# Create database tables
python manage.py makemigrations
python manage.py migrate

# Create admin user and seed roles
python manage.py setup_project --create-admin

# Collect static files
python manage.py collectstatic --noinput
```

### Step 6: Verify Setup

```powershell
python manage.py preflight
```

Expected output: `All preflight checks passed.`

---

## 3. Database Options

### Option A: SQLite (Default — No Setup Required)

SQLite works out of the box on Windows. The database file `db.sqlite3` is created automatically.

Best for: Quick development, single-user testing.

### Option B: PostgreSQL + Redis via Docker Desktop

1. Install Docker Desktop for Windows
2. Start Docker Desktop (wait for it to say "Running")
3. Run:

```powershell
# Start PostgreSQL and Redis
docker compose -f docker-compose.dev.yml up -d

# Wait for databases
python manage.py wait_for_db
```

4. Update `.env`:
```ini
DB_ENGINE=django.db.backends.postgresql
DB_NAME=trust_management
DB_USER=postgres
DB_PASSWORD=devpass
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
```

5. Re-run migrations:
```powershell
python manage.py migrate
python manage.py setup_project --create-admin
```

### Option C: PostgreSQL Installed Locally

1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. During install, set password for `postgres` user
3. Open pgAdmin or psql:
```sql
CREATE DATABASE trust_management;
```
4. Update `.env` with your credentials

---

## 4. Running the Server

### Standard Server (HTTP)

```powershell
python manage.py runserver
```

Open browser: **http://localhost:8000**

### ASGI Server (for WebSocket Chat)

```powershell
pip install daphne
daphne a_core.asgi:application --bind 0.0.0.0 --port 8000
```

### Running on a Different Port

```powershell
python manage.py runserver 0.0.0.0:9000
# Access at http://localhost:9000
```

---

## 5. Seed Test Data

```powershell
python manage.py seed_test_data
```

This creates:

| Username | Password | Role | Use For Testing |
|----------|----------|------|-----------------|
| `admin` | `admin123` | super_admin | Everything (already exists) |
| `manager1` | `Test@12345` | admin | Approvals, user management |
| `member1` | `Test@12345` | member | Donations, expenses, chat |
| `member2` | `Test@12345` | member | Multi-user chat testing |
| `user1` | `Test@12345` | user | Basic browsing, products |
| `ngo_org1` | `Test@12345` | ngo | Fund requests |

Also creates: 4 donation types, 5 expense categories, 5 products, 4 notices, 5 donations, 5 expenses, 2 NGO requests, and 3 transactions.

To remove all test data:
```powershell
python manage.py seed_test_data --cleanup
```

---

## 6. Testing Every Feature

### Start Here

1. Open browser to http://localhost:8000
2. Keep PowerShell/terminal open (you'll see email output and errors here)
3. Open browser DevTools (F12) → Network tab to watch requests

---

### 6.1 Authentication

#### Test: Register New User
1. Go to http://localhost:8000/auth/register/
2. Fill in:
   - Username: `testwindows`
   - Email: `test@windows.local`
   - Password: `Windows@12345`
   - Confirm Password: `Windows@12345`
3. Click "Register"
4. **Check**: Redirected to home page
5. **Check**: Yellow verification banner at top
6. **Check**: Terminal shows email content with verification link
7. Copy the verification URL from terminal → paste in browser → verified

#### Test: Login
1. Go to http://localhost:8000/auth/login/
2. Login as `member1` / `Test@12345`
3. **Check**: Green "Login successful" message
4. **Check**: Navbar shows username

#### Test: Failed Login (Rate Limiting)
1. Go to http://localhost:8000/auth/login/
2. Try logging in with wrong password 5 times
3. **Check**: "Account temporarily locked" message appears

#### Test: Profile & Settings
1. While logged in, go to http://localhost:8000/auth/profile/
2. **Check**: Profile page loads with user info
3. Go to http://localhost:8000/auth/settings/
4. **Check**: Password change form and 2FA section visible

#### Test: 2FA (as admin)
1. Login as `admin` / `admin123`
2. Go to http://localhost:8000/auth/2fa/setup/
3. **Check**: QR code image displayed
4. Scan with Google Authenticator / Authy
5. Enter 6-digit code → Submit
6. **Check**: Backup codes page shown
7. Logout → Login again
8. **Check**: 2FA code entry screen appears
9. Enter code from app → Submit
10. **Check**: Login succeeds

#### Test: Logout
1. Click "Logout" in navbar
2. **Check**: Redirected to login page with success message
3. Try accessing http://localhost:8000/auth/profile/ directly
4. **Check**: Redirected to login (LoginRequired working)

---

### 6.2 Roles & Permissions

#### Test: View Roles (as admin)
1. Login as `admin` / `admin123`
2. Go to http://localhost:8000/roles/
3. **Check**: All users listed with role badges
4. **Check**: Can see manager1 (admin), member1 (member), etc.

#### Test: Assign Role
1. Find `user1` in the list
2. Click "Assign" → Change role to "member"
3. **Check**: Role updated, page refreshes

#### Test: Permission Denial
1. Login as `user1` / `Test@12345`
2. Try accessing http://localhost:8000/dashboard/
3. **Check**: Redirected with "Permission denied" or 403 page
4. Try accessing http://localhost:8000/roles/
5. **Check**: Redirected (not admin)

---

### 6.3 Donations

#### Test: Add Donation (as member)
1. Login as `member1` / `Test@12345`
2. Go to http://localhost:8000/donation/add-donation/
3. Fill in:
   - Donation Type: Select from dropdown (e.g., "General Fund")
   - Display Name: `Windows Test Donor`
   - Amount: `5000`
   - Handover By: `Bank Transfer`
   - Description: `Testing from Windows`
4. Click Submit
5. **Check**: Success message, donation created

#### Test: Admin Donation Management
1. Login as `admin` / `admin123`
2. Go to http://localhost:8000/donation/donations/admin/
3. **Check**: List of all donations with status
4. Find "Windows Test Donor" (pending)
5. Click Approve
6. **Check**: Status changes to Approved

#### Test: Export Donations
1. Still as admin, click Export (or go to `/donation/donations/admin/export/?format=csv`)
2. **Check**: CSV file downloads
3. Open in Excel/Notepad → verify data

---

### 6.4 Expenses

#### Test: Create Expense (as member)
1. Login as `member1` / `Test@12345`
2. Go to http://localhost:8000/expenses/create/
3. Fill in:
   - Title: `Windows Test Expense`
   - Amount: `2500.00`
   - Category: Select from dropdown
   - Description: `Testing expense workflow on Windows`
4. Submit
5. **Check**: Created with "Draft" status
6. Go to http://localhost:8000/expenses/
7. **Check**: Expense listed with "Submit" button
8. Click "Submit"
9. **Check**: Status changes to "Pending"

#### Test: Approve Expense (as admin)
1. Login as `admin` / `admin123`
2. Go to http://localhost:8000/expenses/admin/
3. Filter by "Pending"
4. Find "Windows Test Expense"
5. Click "Approve"
6. **Check**: Status changes to "Approved"
7. Click "Mark Paid"
8. **Check**: Status changes to "Paid"

---

### 6.5 Products & Orders

#### Test: Browse Products
1. Go to http://localhost:8000/products/ (any user or logged out)
2. **Check**: Product grid shows 5 seeded products
3. **Check**: Prices and discounts displayed
4. Click on a product → detail page

#### Test: Place Order (as member)
1. Login as `member1` / `Test@12345`
2. Go to a product detail page
3. Set quantity: 2
4. Click "Order"
5. **Check**: Order placed, success message
6. Go to http://localhost:8000/products/orders/
7. **Check**: Order listed with "Pending" status

#### Test: Admin Product Management
1. Login as `admin` / `admin123`
2. Go to http://localhost:8000/products/admin/products/
3. Click "Create Product"
4. Fill in: Name, Price (99.00), Stock (20), Category
5. Submit
6. **Check**: Product created and listed
7. Go to http://localhost:8000/products/admin/orders/
8. **Check**: All orders visible, can confirm/process

---

### 6.6 Notices

#### Test: Create Notice (as member)
1. Login as `member1` / `Test@12345`
2. Go to http://localhost:8000/notices/create/
3. Fill: Title: `Windows Test Notice`, Content, Priority: High
4. Submit
5. **Check**: Notice created (pending approval)

#### Test: Approve Notice (as admin)
1. Login as `admin`
2. Go to http://localhost:8000/notices/admin/
3. Approve the pending notice
4. **Check**: Notice now visible at http://localhost:8000/notices/

#### Test: Notifications
1. Check navbar for bell icon with unread count
2. Go to http://localhost:8000/notices/notifications/
3. **Check**: Notifications listed
4. Click "Mark All Read"
5. **Check**: Count goes to 0

---

### 6.7 NGO Fund Requests

#### Test: Submit Request (as NGO)
1. Login as `ngo_org1` / `Test@12345`
2. Go to http://localhost:8000/ngo/create/
3. Fill: Title: `Windows Test Request`, Amount: `50000`, Description
4. Submit
5. **Check**: Request created

#### Test: Admin Review
1. Login as `admin`
2. Go to http://localhost:8000/ngo/admin/
3. Find the request, set approved amount to `40000`
4. Click Approve
5. **Check**: Status changes to "Approved"

---

### 6.8 Chat (WebSocket)

> **Important**: Must run with `daphne` for WebSocket support!

```powershell
# Stop runserver, start daphne instead:
daphne a_core.asgi:application --bind 0.0.0.0 --port 8000
```

#### Test: Create Group & Chat
1. Open **Browser 1** (Chrome): Login as `member1`
2. Go to http://localhost:8000/chat/
3. Click "Create Group" → Name: `Windows Test Chat`, add `member2`
4. Open group → chat room loads

5. Open **Browser 2** (Firefox/Edge/Incognito): Login as `member2`
6. Go to http://localhost:8000/chat/
7. Open "Windows Test Chat"

8. In Browser 1: Type "Hello from member1!" → Send
9. **Check**: Message appears in Browser 2 **instantly** (no refresh)
10. In Browser 2: Type "Reply from member2!" → Send
11. **Check**: Message appears in Browser 1 instantly

---

### 6.9 Dashboard & Reports (as admin)

#### Test: Dashboard
1. Login as `admin` / `admin123`
2. Go to http://localhost:8000/dashboard/
3. **Check**: Summary cards (donations total, expenses total, user count)
4. **Check**: Charts render (may need seeded data)

#### Test: Activity Log
1. Go to http://localhost:8000/dashboard/activity/
2. **Check**: List of all actions (logins, donations, approvals)
3. **Check**: Filter works

#### Test: Reports
1. Go to http://localhost:8000/reports/
2. Select "Donations" report, CSV format, last 30 days
3. Click Generate
4. **Check**: Report generated, download link appears
5. Download and verify CSV contents

---

### 6.10 Transparency (Public)

1. Logout or open incognito window
2. Go to http://localhost:8000/transparency/
3. **Check**: Page loads without login
4. **Check**: Shows donation totals, expense breakdowns
5. **Check**: No personal names/emails visible

---

### 6.11 Site Configuration (super_admin)

1. Login as `admin` / `admin123`
2. Go to http://localhost:8000/config/
3. Change "Trust Name" to "Windows Test Trust"
4. Save
5. **Check**: Navbar/header shows new name
6. View page source → meta tags updated

---

### 6.12 Approval Engine

1. Login as `admin`
2. Go to http://localhost:8000/approvals/
3. **Check**: All pending approvals from all modules in one place
4. Approve/reject items with notes
5. **Check**: Original items update status

---

### 6.13 Health & System Endpoints

Open each in browser and verify:

| URL | Expected |
|-----|----------|
| http://localhost:8000/health/live/ | `{"status": "alive"}` |
| http://localhost:8000/health/ready/ | `{"ready": true, ...}` |
| http://localhost:8000/health/ | Health info page |
| http://localhost:8000/robots.txt | Text file with rules |
| http://localhost:8000/sitemap.xml | XML sitemap |
| http://localhost:8000/metrics/ | Prometheus metrics text |

---

## 7. Running Automated Tests

### Run All Tests

```powershell
# Make sure venv is active
.\venv\Scripts\Activate.ps1

# Run all tests
pytest

# Verbose output (see each test name)
pytest -v

# With coverage report
pytest --cov --cov-report=term-missing

# Stop on first failure
pytest -x

# Run specific test file
pytest tests\test_e2e_full_system.py -v

# Run specific test class
pytest tests\test_e2e_full_system.py::TestDonationWorkflow -v

# Run specific test
pytest tests\test_e2e_full_system.py::TestDonationWorkflow::test_member_can_create_donation -v
```

### Test Categories

```powershell
# Security tests
pytest a_customeauth\test_security.py -v

# Integration tests
pytest tests\test_payments.py -v
pytest tests\test_cors.py -v
pytest tests\test_file_validation.py -v

# End-to-end full system
pytest tests\test_e2e_full_system.py -v

# Only fast tests (skip slow/integration)
pytest -m "not slow and not integration"
```

### Expected Output (All Pass)

```
tests/test_e2e_full_system.py::TestPublicEndpoints::test_home_page PASSED
tests/test_e2e_full_system.py::TestPublicEndpoints::test_login_page PASSED
tests/test_e2e_full_system.py::TestPublicEndpoints::test_health_live PASSED
...
============= 50+ passed in 12.34s =============
```

---

## 8. Docker on Windows

### Prerequisites
- Docker Desktop for Windows installed and running
- WSL 2 backend enabled (Docker Desktop settings)

### Full Production Stack

```powershell
# Build and start everything
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f web

# Stop everything
docker compose down
```

### Development Services Only (PostgreSQL + Redis)

```powershell
docker compose -f docker-compose.dev.yml up -d

# Check they're running
docker compose -f docker-compose.dev.yml ps

# Stop
docker compose -f docker-compose.dev.yml down
```

### Monitoring Stack

```powershell
docker compose -f docker-compose.monitoring.yml up -d

# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### Load Testing

```powershell
# Create load test users
python manage.py create_loadtest_users

# Run Locust (web UI)
locust -f loadtests/locustfile.py
# Open http://localhost:8089

# OR headless mode
python -m loadtests.runner --users 50 --spawn-rate 5 --duration 60
```

---

## 9. Common Windows Issues & Fixes

### Issue: `venv\Scripts\Activate.ps1` — Execution Policy Error

```powershell
# Fix: Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate again
.\venv\Scripts\Activate.ps1
```

### Issue: `pip install` fails for `psycopg` or `weasyprint`

```powershell
# psycopg — use binary variant (already in requirements.txt)
pip install "psycopg[binary]==3.2.3"

# weasyprint — needs GTK3
# Download GTK3 installer from: https://github.com/nickvdyck/weasyprint-windows
# OR skip it (PDF receipts won't work, everything else is fine):
pip install -r requirements.txt --ignore-installed weasyprint
```

### Issue: `ModuleNotFoundError: No module named 'services'`

You're running from the wrong directory. Always run from project root:
```powershell
cd "C:\Users\YourName\Desktop\Projects\trust-management-django"
python manage.py runserver
```

### Issue: Port 8000 already in use

```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or use a different port
python manage.py runserver 8001
```

### Issue: `OperationalError: no such table`

```powershell
# Run migrations
python manage.py makemigrations
python manage.py migrate
```

### Issue: Static files not loading (CSS missing)

```powershell
python manage.py collectstatic --noinput

# Verify whitenoise is working (check terminal for 200 on /static/ requests)
```

### Issue: Redis connection error (when using Docker)

```powershell
# Check Docker is running
docker ps

# If containers not started
docker compose -f docker-compose.dev.yml up -d

# If not using Docker, use LocMem cache instead
# Edit .env:
# CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache
```

### Issue: Chat messages not real-time

WebSocket requires ASGI server, not the default runserver:
```powershell
# Use Daphne
daphne a_core.asgi:application --bind 0.0.0.0 --port 8000

# Or ensure CHANNEL_BACKEND is set in .env:
# CHANNEL_BACKEND=channels.layers.InMemoryChannelLayer
```

### Issue: `FileNotFoundError: logs/app.log`

```powershell
# Create logs directory manually
mkdir logs
```

### Issue: `django.db.utils.OperationalError: database is locked` (SQLite)

SQLite doesn't handle concurrent writes well. Solutions:
1. Use only one `runserver` instance at a time
2. Switch to PostgreSQL for multi-process testing
3. Close any SQLite browser tools (DB Browser for SQLite, etc.)

### Issue: Long file paths on Windows (path > 260 chars)

```powershell
# Enable long paths in Windows (run PowerShell as Admin)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Also enable in Git
git config --system core.longpaths true
```

### Issue: Line ending warnings from Git

```powershell
# Configure Git to handle Windows line endings
git config --global core.autocrlf true
```

---

## Quick Reference (PowerShell Commands)

```powershell
# === SETUP ===
.\venv\Scripts\Activate.ps1              # Activate venv
pip install -r requirements.txt           # Install deps
python manage.py migrate                  # Create DB tables
python manage.py setup_project --create-admin  # Create admin user
python manage.py seed_test_data           # Load test data

# === RUN ===
python manage.py runserver                # HTTP server (port 8000)
daphne a_core.asgi:application --bind 0.0.0.0 --port 8000  # ASGI (WebSocket)

# === TEST ===
pytest -v                                 # Run all tests
pytest tests\test_e2e_full_system.py -v   # Full system test
pytest --cov                              # With coverage

# === MAINTENANCE ===
python manage.py preflight                # Verify config
python manage.py security_audit           # Security check
python manage.py backup_db                # Backup database
python manage.py cleanup_data --days 90   # Clean old data

# === DOCKER ===
docker compose -f docker-compose.dev.yml up -d    # Start PG + Redis
docker compose -f docker-compose.dev.yml down      # Stop services
docker compose up -d                               # Full production stack

# === LOAD TEST ===
python manage.py create_loadtest_users    # Seed load test accounts
locust -f loadtests/locustfile.py         # Web UI at :8089
python -m loadtests.runner                # Headless with thresholds
```

---

## Test Accounts Summary

| Step | Login As | Password | What to Test |
|------|----------|----------|--------------|
| 1 | `admin` | `admin123` | Dashboard, config, roles, approvals, reports |
| 2 | `manager1` | `Test@12345` | Approve donations/expenses, manage users |
| 3 | `member1` | `Test@12345` | Create donations, expenses, chat, orders |
| 4 | `member2` | `Test@12345` | Chat (second browser), multi-user flows |
| 5 | `user1` | `Test@12345` | Test permission denial, basic browsing |
| 6 | `ngo_org1` | `Test@12345` | Submit fund requests |
| 7 | Register new | (your choice) | Registration + email verification flow |

---

## Success Criteria

When everything works:

- [ ] Server starts without errors
- [ ] All test accounts can login
- [ ] Admin dashboard shows statistics
- [ ] Donations can be created and approved
- [ ] Expenses flow through draft → pending → approved → paid
- [ ] Products can be ordered
- [ ] Notices appear after approval
- [ ] Chat messages are real-time (with Daphne)
- [ ] Reports generate and download
- [ ] `pytest -v` shows all tests passing
- [ ] Health endpoints return 200

**You're ready for production deployment!**
