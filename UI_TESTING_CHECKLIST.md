# UI Testing Checklist

Use this checklist to verify every feature works correctly through the browser.
Run `python manage.py seed_test_data` first to populate test data.

**Server**: http://localhost:8000
**Test Password**: `Test@12345` (for all test accounts)

---

## Pre-Test Setup

- [ ] Server running (`make run` or `make run-asgi` for WebSocket)
- [ ] Seed data loaded (`python manage.py seed_test_data`)
- [ ] Browser dev tools open (Network tab for checking status codes)
- [ ] Two browser profiles ready (for multi-user testing: chat, approvals)

---

## 1. Authentication Flow

### Register
- [ ] Navigate to `/auth/register/`
- [ ] Attempt submit with empty fields → validation errors shown
- [ ] Attempt weak password (e.g., "password") → complexity error
- [ ] Register with valid data → redirected to home
- [ ] Yellow "Verify email" banner appears at top
- [ ] Check console output for verification email (in development)
- [ ] Verification link works (status changes to verified)

### Login
- [ ] Navigate to `/auth/login/`
- [ ] Login with `member1` / `Test@12345` → success message, redirected to home
- [ ] Navbar shows username and avatar
- [ ] Try 5 wrong passwords → account locked message on 5th attempt
- [ ] Wait or clear cache, then login successfully

### Profile
- [ ] Navigate to `/auth/profile/`
- [ ] Update first name and last name → saved
- [ ] Update avatar (upload image) → image shows
- [ ] Role and recent activity displayed

### Password Change
- [ ] Navigate to `/auth/settings/`
- [ ] Change password → success message
- [ ] Login with new password works
- [ ] Reset back to `Test@12345` for other tests

### 2FA (Test as admin)
- [ ] Login as `admin` / `admin123`
- [ ] Go to `/auth/settings/` → 2FA section visible
- [ ] Click "Enable 2FA" → QR code displayed
- [ ] Scan with authenticator app → enter code → backup codes shown
- [ ] Logout and login → 2FA verification screen appears
- [ ] Enter correct code → login succeeds
- [ ] Disable 2FA from settings (requires password)

### Logout
- [ ] Click logout button → logged out, redirected to login
- [ ] Try accessing `/dashboard/` → redirected to login (LoginRequired)

---

## 2. Role Management (Login as `admin`)

- [ ] Navigate to `/roles/`
- [ ] All users listed with their current roles
- [ ] Click assign on `user1` → change to "member" → saved
- [ ] Navigate to `/roles/members/` → members directory shows
- [ ] Toggle active status on a user → status changes

### Role Requests (Login as `member1`)
- [ ] Navigate to `/roles/request/`
- [ ] Submit request for "admin" role with justification
- [ ] Message confirms submission

### Approve Role Request (Login as `admin`)
- [ ] Navigate to `/roles/pending/`
- [ ] See pending request from member1
- [ ] Approve → role updated
- [ ] (Revert role back to member for other tests)

---

## 3. Donations

### Add Donation (Login as `member1`)
- [ ] Navigate to `/donation/add-donation/`
- [ ] Fill form: donor name, amount, type (from dropdown), description
- [ ] Submit → success message
- [ ] Donation appears with "Pending" status

### Manage Donations (Login as `admin`)
- [ ] Navigate to `/donation/donations/admin/`
- [ ] See list with approved and pending donations
- [ ] Approve a pending donation → status changes to approved
- [ ] Reject a donation → removed from pending
- [ ] Export button → CSV downloads

### View Donation Types
- [ ] Navigate to `/donation/donation/`
- [ ] All donation types listed with descriptions
- [ ] Click on a type → detail page

---

## 4. Expenses

### Create Expense (Login as `member1`)
- [ ] Navigate to `/expenses/create/`
- [ ] Fill: title, amount, category (dropdown), description
- [ ] Submit → expense created as "Draft"
- [ ] Navigate to `/expenses/` → see my expenses

### Submit for Approval
- [ ] On expense list, click "Submit" on a draft expense
- [ ] Status changes to "Pending"

### Admin Workflow (Login as `admin`)
- [ ] Navigate to `/expenses/admin/`
- [ ] Filter by status: pending
- [ ] Approve an expense → status becomes "Approved"
- [ ] Mark paid → status becomes "Paid"
- [ ] Reject an expense → enter reason → status becomes "Rejected"
- [ ] Export → CSV downloads

---

## 5. Payments & Receipts

### Make Payment (Login as `member1`)
- [ ] Navigate to `/payments/`
- [ ] Select type (membership), enter amount
- [ ] Submit → transaction created

### Payment History
- [ ] Navigate to `/payments/history/`
- [ ] See all transactions with status
- [ ] Click "Download Receipt" on a completed transaction
- [ ] PDF downloads (check file opens correctly)

### Admin View (Login as `admin`)
- [ ] Navigate to `/payments/admin/`
- [ ] All transactions visible
- [ ] Export button works

---

## 6. Notices & Notifications

### Create Notice (Login as `member1`)
- [ ] Navigate to `/notices/create/`
- [ ] Fill: title, content, priority (dropdown), expiry date
- [ ] Submit → notice created (pending approval)

### Approve Notice (Login as `admin`)
- [ ] Navigate to `/notices/admin/`
- [ ] See pending notice
- [ ] Approve → notice becomes active

### View Notices (Any user)
- [ ] Navigate to `/notices/`
- [ ] Active, approved notices displayed
- [ ] Priority badges shown (high = red, medium = yellow, low = green)

### Notifications
- [ ] Bell icon in navbar shows unread count
- [ ] Click → notifications page
- [ ] Mark individual as read
- [ ] "Mark All Read" button works

---

## 7. Products & Orders

### Browse Products (Any user)
- [ ] Navigate to `/products/`
- [ ] Products grid displayed with prices and discount badges
- [ ] Click product → detail page with description

### Place Order (Login as `member1`)
- [ ] On product detail, click "Order"
- [ ] Set quantity → submit
- [ ] Order confirmation shown
- [ ] Navigate to `/products/orders/` → see order with "Pending" status
- [ ] Cancel order → status changes to "Cancelled"

### Admin Product Management (Login as `admin`)
- [ ] Navigate to `/products/admin/products/`
- [ ] Create new product (name, price, stock, category, discount)
- [ ] Edit existing product → changes saved
- [ ] Navigate to `/products/admin/orders/`
- [ ] Confirm/process/deliver orders

---

## 8. NGO Fund Requests

### Submit Request (Login as `ngo_org1`)
- [ ] Navigate to `/ngo/create/`
- [ ] Fill: title, description, amount, attach document (optional)
- [ ] Submit → request created as "Pending"
- [ ] Navigate to `/ngo/` → see my requests

### Admin Review (Login as `admin`)
- [ ] Navigate to `/ngo/admin/`
- [ ] See pending/under_review requests
- [ ] Review: set approved amount, add notes
- [ ] Approve → status changes
- [ ] Reject → status changes with reason

---

## 9. Chat (Requires ASGI: `make run-asgi`)

### Create Group (Login as `member1`)
- [ ] Navigate to `/chat/`
- [ ] Click "Create Group"
- [ ] Name: "Test Group", add `member2` as member
- [ ] Group created and listed

### Real-Time Messaging
- [ ] Open group in Browser 1 (as `member1`)
- [ ] Open same group in Browser 2 (as `member2`)
- [ ] Send message from Browser 1 → appears instantly in Browser 2
- [ ] Send from Browser 2 → appears in Browser 1
- [ ] Messages persist (refresh page → messages still there)

### Manage Members
- [ ] As group creator, click "Manage Members"
- [ ] Add/remove a member → list updates

---

## 10. Dashboard & Reports (Login as `admin`)

### Dashboard
- [ ] Navigate to `/dashboard/`
- [ ] Statistics cards: total donations, expenses, users, balance
- [ ] Charts render correctly (donations over time, expense categories)
- [ ] Recent activity list shows latest actions

### Activity Log
- [ ] Navigate to `/dashboard/activity/`
- [ ] Chronological list of all system actions
- [ ] Filter by category (auth, donation, expense, etc.)
- [ ] Export button works

### Generate Reports
- [ ] Navigate to `/reports/`
- [ ] Generate donations report (CSV) → downloads
- [ ] Generate expenses report (PDF) → downloads
- [ ] Generate members report → downloads
- [ ] Set date range → only matching records included

---

## 11. Transparency (Public)
- [ ] Logout (or use incognito)
- [ ] Navigate to `/transparency/`
- [ ] Page loads without login
- [ ] Shows aggregated donation totals
- [ ] Shows expense summaries
- [ ] No personal information (names, emails) visible

---

## 12. Approval Engine (Login as `admin`)
- [ ] Navigate to `/approvals/`
- [ ] All pending items from across the system shown
- [ ] Approve with notes → item status updated
- [ ] Reject with notes → item status updated
- [ ] Original requester would receive notification

---

## 13. Site Configuration (Login as `admin`)
- [ ] Navigate to `/config/`
- [ ] Edit trust name → reflected in navbar/footer
- [ ] Edit contact email → reflected in security.txt
- [ ] Edit meta title/description → reflected in page source
- [ ] Save → success message

---

## 14. Security & Edge Cases

### CSRF Protection
- [ ] Open browser dev tools → disable cookies → submit form
- [ ] `/csrf_failure.html` error page shown (not a server error)

### Rate Limiting
- [ ] Rapidly refresh a page 100+ times in 60 seconds
- [ ] "429 Too Many Requests" page shown

### Session Timeout
- [ ] Login, then wait 30+ minutes (or set SESSION_IDLE_TIMEOUT=60 in .env)
- [ ] Next action → redirected to login with "session expired" message

### File Upload Validation
- [ ] Try uploading a .exe file as expense receipt → rejected
- [ ] Try uploading file > 5MB → rejected
- [ ] Upload valid PDF/image → accepted

### 404 Page
- [ ] Navigate to `/nonexistent-page/`
- [ ] Styled 404 page shown (not Django debug page)

### Permission Denied
- [ ] Login as `user1` (user role)
- [ ] Try accessing `/dashboard/` → redirected with "permission denied"
- [ ] Try accessing `/expenses/admin/` → redirected

---

## 15. Health & System Endpoints

- [ ] GET `/health/live/` → `{"status": "alive"}` (200)
- [ ] GET `/health/ready/` → `{"ready": true, ...}` (200)
- [ ] GET `/health/` → `{"status": "healthy"}` (200)
- [ ] GET `/robots.txt` → text response with Disallow rules
- [ ] GET `/sitemap.xml` → XML with URL entries
- [ ] GET `/.well-known/security.txt` → Contact info
- [ ] GET `/metrics/` → Prometheus format metrics

---

## Test Completion

When all boxes are checked:
1. Run automated tests: `make test`
2. Run smoke test: `bash scripts/smoke-test.sh`
3. Check for console errors in browser dev tools
4. Verify no broken links (check Network tab for 404s)

**All tests passing = System ready for deployment!**
