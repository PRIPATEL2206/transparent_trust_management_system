import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client

from donations.models import DonationType, Donation
from expenses.models import Expense, ExpenseCategory
from roles.models import UserRole


@pytest.mark.django_db
class TestDonationExport:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='expuser', password='SecurePass123!@#', email='exp@test.com'
        )
        self.admin = User.objects.create_user(
            username='expadmin', password='AdminPass123!@#', email='expadmin@test.com'
        )
        role = UserRole.objects.get(user=self.admin)
        role.role = 'admin'
        role.approved = True
        role.save()

        self.donation_type = DonationType.objects.create(
            name='Export Fund', desc='For export tests', created_by=self.admin
        )
        cache.clear()

    def test_export_requires_admin(self):
        self.client.login(username='expuser', password='SecurePass123!@#')
        response = self.client.get('/donation/donations/admin/export/')
        assert response.status_code == 302

    def test_export_returns_csv_content_type(self):
        self.client.login(username='expadmin', password='AdminPass123!@#')
        response = self.client.get('/donation/donations/admin/export/')
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']

    def test_export_contains_header_row(self):
        self.client.login(username='expadmin', password='AdminPass123!@#')
        response = self.client.get('/donation/donations/admin/export/')
        content = response.content.decode('utf-8')
        first_line = content.split('\n')[0]
        assert 'Amount' in first_line or 'amount' in first_line.lower()

    def test_export_includes_approved_donations(self):
        Donation.objects.create(
            add_by=self.user, donation_for=self.donation_type,
            amount=5000, display_name='Export Visible', handover_by='Cash',
            is_approved=True
        )
        self.client.login(username='expadmin', password='AdminPass123!@#')
        response = self.client.get('/donation/donations/admin/export/')
        assert b'Export Visible' in response.content

    def test_export_excludes_unapproved_donations(self):
        Donation.objects.create(
            add_by=self.user, donation_for=self.donation_type,
            amount=1000, display_name='Not Approved Yet', handover_by='Cash',
            is_approved=False
        )
        self.client.login(username='expadmin', password='AdminPass123!@#')
        response = self.client.get('/donation/donations/admin/export/')
        assert b'Not Approved Yet' not in response.content

    def test_export_rate_limited_after_threshold(self):
        self.client.login(username='expadmin', password='AdminPass123!@#')
        for _ in range(5):
            self.client.post('/donation/donations/admin/export/')

        response = self.client.post('/donation/donations/admin/export/')
        assert response.status_code == 429


@pytest.mark.django_db
class TestExpenseExport:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='exexpuser', password='SecurePass123!@#', email='exexp@test.com'
        )
        self.admin = User.objects.create_user(
            username='exexpadmin', password='AdminPass123!@#', email='exexpadm@test.com'
        )
        role = UserRole.objects.get(user=self.admin)
        role.role = 'admin'
        role.approved = True
        role.save()

        self.category = ExpenseCategory.objects.create(name='Export Cat', is_active=True)
        cache.clear()

    def test_export_requires_admin(self):
        self.client.login(username='exexpuser', password='SecurePass123!@#')
        response = self.client.get('/expenses/admin/export/')
        assert response.status_code == 302

    def test_export_returns_csv(self):
        self.client.login(username='exexpadmin', password='AdminPass123!@#')
        response = self.client.get('/expenses/admin/export/')
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']

    def test_export_contains_expense_data(self):
        Expense.objects.create(
            raised_by=self.user, title='Export Expense', description='Test',
            amount=Decimal('250.00'), category=self.category, status='approved'
        )
        self.client.login(username='exexpadmin', password='AdminPass123!@#')
        response = self.client.get('/expenses/admin/export/')
        assert b'Export Expense' in response.content

    def test_export_can_filter_by_status(self):
        Expense.objects.create(
            raised_by=self.user, title='Paid One', description='D',
            amount=100, category=self.category, status='paid'
        )
        Expense.objects.create(
            raised_by=self.user, title='Pending One', description='D',
            amount=100, category=self.category, status='pending'
        )
        self.client.login(username='exexpadmin', password='AdminPass123!@#')
        response = self.client.get('/expenses/admin/export/?status=paid')
        assert b'Paid One' in response.content
        assert b'Pending One' not in response.content

    def test_export_rate_limited(self):
        self.client.login(username='exexpadmin', password='AdminPass123!@#')
        for _ in range(5):
            self.client.post('/expenses/admin/export/')
        response = self.client.post('/expenses/admin/export/')
        assert response.status_code == 429


@pytest.mark.django_db
class TestExportRowCap:

    def setup_method(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='capadmin', password='AdminPass123!@#', email='cap@test.com'
        )
        role = UserRole.objects.get(user=self.admin)
        role.role = 'admin'
        role.approved = True
        role.save()

        self.donation_type = DonationType.objects.create(
            name='Bulk Fund', desc='Bulk test', created_by=self.admin
        )
        cache.clear()

    def test_donation_export_caps_at_10000(self):
        Donation.objects.bulk_create([
            Donation(
                add_by=self.admin, donation_for=self.donation_type,
                amount=10, display_name=f'Donor{i}', handover_by='X',
                is_approved=True
            ) for i in range(50)
        ])
        self.client.login(username='capadmin', password='AdminPass123!@#')
        response = self.client.get('/donation/donations/admin/export/')
        assert response.status_code == 200
        lines = response.content.decode('utf-8').strip().split('\n')
        assert len(lines) <= 10001  # header + up to 10000 rows


@pytest.mark.django_db
class TestRateLimitDecorator:

    def setup_method(self):
        self.client = Client()
        cache.clear()

    def test_rate_limit_only_on_post(self):
        for _ in range(10):
            response = self.client.get('/auth/login/')
            assert response.status_code == 200

    def test_rate_limit_blocks_after_threshold(self):
        for i in range(5):
            self.client.post('/auth/login/', {
                'username': f'baduser{i}', 'password': 'wrong'
            })
        response = self.client.post('/auth/login/', {
            'username': 'baduser', 'password': 'wrong'
        })
        assert response.status_code == 429

    def test_successful_login_not_counted(self):
        user = User.objects.create_user(username='rluser', password='SecurePass123!@#')
        for _ in range(4):
            self.client.post('/auth/login/', {
                'username': 'rluser', 'password': 'SecurePass123!@#'
            })
            self.client.logout()
        response = self.client.post('/auth/login/', {
            'username': 'rluser', 'password': 'SecurePass123!@#'
        })
        assert response.status_code == 302
