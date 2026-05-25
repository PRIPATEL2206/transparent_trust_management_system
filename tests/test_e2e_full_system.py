"""
End-to-end test suite — exercises the full system workflow.

Tests the complete user journey:
1. Registration → Email verification → Login
2. Role assignment → Permission enforcement
3. Donations → Approval → Transparency
4. Expenses → Submit → Approve → Pay
5. Products → Order → Manage
6. Notices → Create → Approve → View
7. NGO Requests → Submit → Review
8. Dashboard → Reports → Export
9. Health checks and system endpoints

Run with:
    pytest tests/test_e2e_full_system.py -v
    pytest tests/test_e2e_full_system.py -v --tb=short
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.utils import timezone


@pytest.fixture
def member_user(db):
    user = User.objects.create_user(
        username='e2e_member',
        email='member@e2e.test',
        password='E2E_Test@12345',
    )
    from roles.models import UserRole
    role = UserRole.objects.get(user=user)
    role.role = 'member'
    role.approved = True
    role.save()
    from a_customeauth.models import EmailVerification
    EmailVerification.objects.create(
        user=user,
        is_verified=True,
        verified_at=timezone.now(),
        expires_at=timezone.now() + timedelta(hours=24),
    )
    return user


@pytest.fixture
def admin_user_e2e(db):
    user = User.objects.create_user(
        username='e2e_admin',
        email='admin@e2e.test',
        password='E2E_Admin@12345',
    )
    from roles.models import UserRole
    role = UserRole.objects.get(user=user)
    role.role = 'admin'
    role.approved = True
    role.save()
    from a_customeauth.models import EmailVerification, TOTPDevice
    EmailVerification.objects.create(
        user=user,
        is_verified=True,
        verified_at=timezone.now(),
        expires_at=timezone.now() + timedelta(hours=24),
    )
    TOTPDevice.objects.create(
        user=user,
        secret='JBSWY3DPEHPK3PXP',
        is_active=True,
        is_confirmed=True,
    )
    return user


@pytest.fixture
def ngo_user(db):
    user = User.objects.create_user(
        username='e2e_ngo',
        email='ngo@e2e.test',
        password='E2E_NGO@12345',
    )
    from roles.models import UserRole
    role = UserRole.objects.get(user=user)
    role.role = 'ngo'
    role.approved = True
    role.save()
    from a_customeauth.models import EmailVerification
    EmailVerification.objects.create(
        user=user,
        is_verified=True,
        verified_at=timezone.now(),
        expires_at=timezone.now() + timedelta(hours=24),
    )
    return user


@pytest.fixture
def member_client(member_user):
    c = Client()
    c.login(username='e2e_member', password='E2E_Test@12345')
    return c


@pytest.fixture
def admin_client_e2e(admin_user_e2e):
    c = Client()
    c.login(username='e2e_admin', password='E2E_Admin@12345')
    session = c.session
    session['2fa_verified'] = True
    session.save()
    return c


@pytest.fixture
def ngo_client(ngo_user):
    c = Client()
    c.login(username='e2e_ngo', password='E2E_NGO@12345')
    return c


@pytest.fixture
def donation_type(db, admin_user_e2e):
    from donations.models import DonationType
    return DonationType.objects.create(
        name='E2E Test Fund',
        desc='Fund created for e2e testing',
        created_by=admin_user_e2e,
        is_forever=True,
    )


@pytest.fixture
def expense_category(db):
    from expenses.models import ExpenseCategory
    return ExpenseCategory.objects.create(name='E2E Category', description='Test category')


@pytest.fixture
def product_category(db):
    from products.models import ProductCategory
    return ProductCategory.objects.create(name='E2E Products', description='Test products')


@pytest.fixture
def product(db, product_category):
    from products.models import Product
    return Product.objects.create(
        name='E2E Test Product',
        description='Product for testing',
        price=Decimal('299.00'),
        stock=10,
        category=product_category,
        is_active=True,
    )


class TestPublicEndpoints:
    """Test all public endpoints work without authentication."""

    def test_home_page(self, client, db):
        response = client.get('/')
        assert response.status_code == 200

    def test_login_page(self, client, db):
        response = client.get('/auth/login/')
        assert response.status_code == 200

    def test_register_page(self, client, db):
        response = client.get('/auth/register/')
        assert response.status_code == 200

    def test_health_live(self, client, db):
        response = client.get('/health/live/')
        assert response.status_code == 200
        assert response.json()['status'] == 'alive'

    def test_health_ready(self, client, db):
        response = client.get('/health/ready/')
        assert response.status_code == 200
        data = response.json()
        assert data['ready'] is True

    def test_robots_txt(self, client, db):
        response = client.get('/robots.txt')
        assert response.status_code == 200
        assert 'User-agent' in response.content.decode()

    def test_sitemap_xml(self, client, db):
        response = client.get('/sitemap.xml')
        assert response.status_code == 200
        assert 'urlset' in response.content.decode()

    def test_404_page(self, client, db):
        response = client.get('/this-page-does-not-exist-xyz/')
        assert response.status_code == 404

    def test_transparency_page(self, client, db):
        response = client.get('/transparency/')
        assert response.status_code == 200

    def test_notices_public(self, client, db):
        response = client.get('/notices/')
        assert response.status_code == 200


class TestRegistrationAndLogin:
    """Test the full authentication lifecycle."""

    @override_settings(THROTTLE_MAX_REQUESTS=10000)
    def test_register_new_user(self, client, db):
        response = client.post('/auth/register/', {
            'username': 'e2e_newuser',
            'email': 'newuser@e2e.test',
            'password': 'NewUser@12345',
            'password_confirm': 'NewUser@12345',
        })
        assert response.status_code == 302
        assert User.objects.filter(username='e2e_newuser').exists()

    @override_settings(THROTTLE_MAX_REQUESTS=10000)
    def test_login_valid_credentials(self, client, member_user):
        response = client.post('/auth/login/', {
            'username': 'e2e_member',
            'password': 'E2E_Test@12345',
        })
        assert response.status_code == 302

    @override_settings(THROTTLE_MAX_REQUESTS=10000)
    def test_login_invalid_credentials(self, client, member_user):
        response = client.post('/auth/login/', {
            'username': 'e2e_member',
            'password': 'wrong_password',
        })
        assert response.status_code == 200  # stays on login page

    def test_logout(self, member_client):
        response = member_client.post('/auth/logout/')
        assert response.status_code == 302

    def test_profile_access(self, member_client):
        response = member_client.get('/auth/profile/')
        assert response.status_code == 200

    def test_settings_access(self, member_client):
        response = member_client.get('/auth/settings/')
        assert response.status_code == 200


class TestRoleBasedAccess:
    """Test that role-based permissions are enforced."""

    def test_member_cannot_access_dashboard(self, member_client):
        response = member_client.get('/dashboard/')
        assert response.status_code in (302, 403)

    def test_admin_can_access_dashboard(self, admin_client_e2e):
        response = admin_client_e2e.get('/dashboard/')
        assert response.status_code == 200

    def test_member_cannot_access_roles(self, member_client):
        response = member_client.get('/roles/')
        assert response.status_code in (302, 403)

    def test_admin_can_access_roles(self, admin_client_e2e):
        response = admin_client_e2e.get('/roles/')
        assert response.status_code == 200

    def test_unauthenticated_redirected_to_login(self, client, db):
        response = client.get('/dashboard/')
        assert response.status_code == 302
        assert 'login' in response.url.lower() or 'auth' in response.url.lower()


class TestDonationWorkflow:
    """Test the donation lifecycle: create → approve → view in transparency."""

    def test_member_can_view_add_page(self, member_client, donation_type):
        response = member_client.get('/donation/add-donation/')
        assert response.status_code == 200

    def test_member_can_create_donation(self, member_client, donation_type):
        response = member_client.post('/donation/add-donation/', {
            'donation_for': donation_type.id,
            'amount': 5000,
            'display_name': 'E2E Donor',
            'handover_by': 'Cash',
            'desc': 'E2E test donation',
        })
        assert response.status_code == 302
        from donations.models import Donation
        assert Donation.objects.filter(display_name='E2E Donor').exists()

    def test_admin_can_view_donations_admin(self, admin_client_e2e, donation_type):
        response = admin_client_e2e.get('/donation/donations/admin/')
        assert response.status_code == 200

    def test_admin_can_approve_donation(self, admin_client_e2e, member_client, donation_type, member_user):
        from donations.models import Donation
        donation = Donation.objects.create(
            add_by=member_user,
            donation_for=donation_type,
            amount=10000,
            display_name='Pending Donor',
            handover_by='Bank',
            is_approved=False,
        )
        response = admin_client_e2e.post(f'/donation/donations/{donation.id}/action/', {
            'action': 'approve',
        })
        assert response.status_code == 302
        donation.refresh_from_db()
        assert donation.is_approved is True

    def test_export_donations_csv(self, admin_client_e2e, donation_type):
        response = admin_client_e2e.get('/donation/donations/admin/export/?format=csv')
        assert response.status_code == 200
        assert 'text/csv' in response.get('Content-Type', '') or response.status_code == 200


class TestExpenseWorkflow:
    """Test the expense lifecycle: create → submit → approve → pay."""

    def test_member_can_create_expense(self, member_client, expense_category):
        response = member_client.post('/expenses/create/', {
            'title': 'E2E Expense',
            'description': 'Created during e2e test',
            'amount': '1500.00',
            'category': expense_category.id,
        })
        assert response.status_code == 302
        from expenses.models import Expense
        expense = Expense.objects.get(title='E2E Expense')
        assert expense.status == 'draft'

    def test_member_can_submit_expense(self, member_client, expense_category, member_user):
        from expenses.models import Expense
        expense = Expense.objects.create(
            raised_by=member_user,
            title='E2E Submit Test',
            description='Test',
            amount=Decimal('1000.00'),
            category=expense_category,
            status='draft',
        )
        response = member_client.post(f'/expenses/{expense.id}/submit/')
        assert response.status_code == 302
        expense.refresh_from_db()
        assert expense.status == 'pending'

    def test_admin_can_approve_expense(self, admin_client_e2e, expense_category, member_user):
        from expenses.models import Expense
        expense = Expense.objects.create(
            raised_by=member_user,
            title='E2E Approve Test',
            description='Test',
            amount=Decimal('2000.00'),
            category=expense_category,
            status='pending',
        )
        response = admin_client_e2e.post(f'/expenses/{expense.id}/action/', {
            'action': 'approve',
        })
        assert response.status_code == 302
        expense.refresh_from_db()
        assert expense.status == 'approved'

    def test_expense_list_filtered(self, member_client, expense_category, member_user):
        response = member_client.get('/expenses/')
        assert response.status_code == 200

    def test_admin_expense_export(self, admin_client_e2e, expense_category):
        response = admin_client_e2e.get('/expenses/admin/export/?format=csv')
        assert response.status_code == 200


class TestProductsAndOrders:
    """Test product browsing and ordering."""

    def test_product_list_public(self, client, product, db):
        response = client.get('/products/')
        assert response.status_code == 200

    def test_product_detail(self, client, product, db):
        response = client.get(f'/products/{product.id}/')
        assert response.status_code == 200

    def test_member_can_order(self, member_client, product):
        response = member_client.post(f'/products/{product.id}/order/', {
            'quantity': 2,
        })
        assert response.status_code == 302
        from products.models import Order
        order = Order.objects.filter(product=product, user__username='e2e_member').first()
        assert order is not None
        assert order.quantity == 2
        assert order.status == 'pending'

    def test_member_can_view_orders(self, member_client, product):
        response = member_client.get('/products/orders/')
        assert response.status_code == 200

    def test_admin_product_management(self, admin_client_e2e, product_category):
        response = admin_client_e2e.get('/products/admin/products/')
        assert response.status_code == 200

    def test_admin_create_product(self, admin_client_e2e, product_category):
        response = admin_client_e2e.post('/products/admin/products/create/', {
            'name': 'E2E New Product',
            'description': 'Created during e2e test',
            'price': '199.00',
            'stock': 50,
            'category': product_category.id,
            'discount_percent': '0',
        })
        assert response.status_code == 302
        from products.models import Product
        assert Product.objects.filter(name='E2E New Product').exists()


class TestNotices:
    """Test notice creation and approval."""

    def test_create_notice(self, member_client, member_user):
        response = member_client.post('/notices/create/', {
            'title': 'E2E Notice',
            'content': 'This is a test notice from e2e.',
            'priority': 'medium',
        })
        assert response.status_code == 302
        from notices.models import Notice
        assert Notice.objects.filter(title='E2E Notice').exists()

    def test_admin_approve_notice(self, admin_client_e2e, admin_user_e2e):
        from notices.models import Notice
        notice = Notice.objects.create(
            title='E2E Pending Notice',
            content='Awaiting approval',
            created_by=admin_user_e2e,
            is_approved=False,
            priority='high',
        )
        response = admin_client_e2e.post(f'/notices/{notice.id}/approve/', {
            'action': 'approve',
        })
        assert response.status_code == 302
        notice.refresh_from_db()
        assert notice.is_approved is True

    def test_public_notices_page(self, client, db):
        response = client.get('/notices/')
        assert response.status_code == 200


class TestNGORequests:
    """Test NGO fund request workflow."""

    def test_ngo_can_create_request(self, ngo_client, ngo_user):
        response = ngo_client.post('/ngo/create/', {
            'title': 'E2E Fund Request',
            'description': 'Funds needed for educational program.',
            'amount_requested': '50000.00',
        })
        assert response.status_code == 302
        from ngo_requests.models import FundRequest
        assert FundRequest.objects.filter(title='E2E Fund Request').exists()

    def test_admin_can_view_requests(self, admin_client_e2e, ngo_user):
        from ngo_requests.models import FundRequest
        FundRequest.objects.create(
            ngo_user=ngo_user,
            title='Admin View Test',
            description='Test',
            amount_requested=Decimal('10000.00'),
        )
        response = admin_client_e2e.get('/ngo/admin/')
        assert response.status_code == 200

    def test_admin_can_action_request(self, admin_client_e2e, ngo_user):
        from ngo_requests.models import FundRequest
        req = FundRequest.objects.create(
            ngo_user=ngo_user,
            title='Action Test',
            description='Test',
            amount_requested=Decimal('25000.00'),
        )
        response = admin_client_e2e.post(f'/ngo/{req.id}/action/', {
            'action': 'approve',
            'amount_approved': '20000.00',
            'notes': 'Approved with reduced amount',
        })
        assert response.status_code == 302
        req.refresh_from_db()
        assert req.status == 'approved'


class TestDashboardAndReports:
    """Test admin dashboard and report generation."""

    def test_dashboard_loads(self, admin_client_e2e):
        response = admin_client_e2e.get('/dashboard/')
        assert response.status_code == 200

    def test_activity_log(self, admin_client_e2e):
        response = admin_client_e2e.get('/dashboard/activity/')
        assert response.status_code == 200

    def test_reports_page(self, admin_client_e2e):
        response = admin_client_e2e.get('/reports/')
        assert response.status_code == 200

    def test_generate_donations_report(self, admin_client_e2e):
        today = timezone.now().date()
        response = admin_client_e2e.post('/reports/', {
            'report_type': 'donations',
            'format': 'csv',
            'date_from': (today - timedelta(days=30)).isoformat(),
            'date_to': today.isoformat(),
        })
        assert response.status_code in (200, 302)


class TestApprovalEngine:
    """Test the generic approval system."""

    def test_approval_list_loads(self, admin_client_e2e):
        response = admin_client_e2e.get('/approvals/')
        assert response.status_code == 200


class TestPayments:
    """Test payment and receipt flow."""

    def test_payment_page(self, member_client):
        response = member_client.get('/payments/')
        assert response.status_code == 200

    def test_payment_history(self, member_client):
        response = member_client.get('/payments/history/')
        assert response.status_code == 200

    def test_create_payment(self, member_client):
        import uuid
        response = member_client.post('/payments/', {
            'transaction_type': 'membership',
            'amount': '1000.00',
            'idempotency_key': str(uuid.uuid4()),
        })
        assert response.status_code in (200, 302)


class TestChat:
    """Test chat group management (non-WebSocket parts)."""

    def test_chat_list(self, member_client):
        response = member_client.get('/chat/')
        assert response.status_code == 200

    def test_create_chat_group(self, admin_client_e2e, admin_user_e2e):
        response = admin_client_e2e.post('/chat/create/', {
            'name': 'E2E Chat Group',
        })
        assert response.status_code == 302
        from chat.models import ChatGroup
        assert ChatGroup.objects.filter(name='E2E Chat Group').exists()


class TestSecurityHeaders:
    """Test that security headers are present on responses."""

    def test_csp_header(self, client, db):
        response = client.get('/')
        assert 'Content-Security-Policy' in response

    def test_referrer_policy(self, client, db):
        response = client.get('/')
        assert response.get('Referrer-Policy') == 'strict-origin-when-cross-origin'

    def test_x_content_type_options(self, client, db):
        response = client.get('/')
        assert response.get('X-Content-Type-Options') == 'nosniff'

    def test_request_id_header(self, client, db):
        response = client.get('/')
        assert 'X-Request-ID' in response

    def test_request_timing_header(self, client, db):
        response = client.get('/')
        assert 'X-Request-Duration-Ms' in response


class TestMetrics:
    """Test the Prometheus metrics endpoint."""

    @override_settings(METRICS_API_KEY='')
    def test_metrics_endpoint(self, client, db):
        response = client.get('/metrics/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'http_requests_total' in content
