#!/bin/bash
# Post-deployment smoke test — verifies critical endpoints respond correctly.
# Usage: ./scripts/smoke-test.sh [base_url]
set -e

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0

check() {
    local name="$1"
    local url="$2"
    local expected_status="$3"
    local body_contains="$4"

    status=$(curl -s -o /tmp/smoke_body -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    body=$(cat /tmp/smoke_body 2>/dev/null || echo "")

    if [ "$status" != "$expected_status" ]; then
        echo "  FAIL  $name — expected $expected_status, got $status"
        FAIL=$((FAIL + 1))
        return
    fi

    if [ -n "$body_contains" ] && ! echo "$body" | grep -q "$body_contains"; then
        echo "  FAIL  $name — body missing: $body_contains"
        FAIL=$((FAIL + 1))
        return
    fi

    echo "  PASS  $name"
    PASS=$((PASS + 1))
}

echo "============================================"
echo " Smoke Test: $BASE_URL"
echo "============================================"
echo ""

# Core health
check "Liveness probe"         "$BASE_URL/health/live/"    "200" "alive"
check "Readiness probe"        "$BASE_URL/health/ready/"   "200" "ready"
check "Health endpoint"        "$BASE_URL/health/"         "200" ""

# Public pages
check "Home page"              "$BASE_URL/"                "200" ""
check "Login page"             "$BASE_URL/auth/login/"     "200" "login"
check "Transparency page"      "$BASE_URL/transparency/"   "200" ""

# SEO / well-known
check "robots.txt"             "$BASE_URL/robots.txt"      "200" "User-agent"
check "sitemap.xml"            "$BASE_URL/sitemap.xml"     "200" "urlset"
check "security.txt"           "$BASE_URL/.well-known/security.txt"  "200" "Contact"

# Security headers
echo ""
echo "Checking security headers..."
headers=$(curl -sI "$BASE_URL/" 2>/dev/null)

check_header() {
    local header_name="$1"
    if echo "$headers" | grep -qi "$header_name"; then
        echo "  PASS  Header: $header_name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  Header: $header_name missing"
        FAIL=$((FAIL + 1))
    fi
}

check_header "X-Content-Type-Options"
check_header "X-Request-ID"
check_header "Referrer-Policy"
check_header "Content-Security-Policy"

# Error pages
check "404 handler"            "$BASE_URL/nonexistent-page-xyz/"  "404" "Not Found"

# Metrics (if accessible)
metrics_status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/metrics/" 2>/dev/null || echo "000")
if [ "$metrics_status" = "200" ] || [ "$metrics_status" = "401" ]; then
    echo "  PASS  Metrics endpoint responding ($metrics_status)"
    PASS=$((PASS + 1))
else
    echo "  WARN  Metrics endpoint: $metrics_status (may be expected if behind auth)"
fi

echo ""
echo "============================================"
echo " Results: $PASS passed, $FAIL failed"
echo "============================================"

if [ $FAIL -gt 0 ]; then
    exit 1
fi
echo "All smoke tests passed."
