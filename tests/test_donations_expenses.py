import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client

from donations.models import DonationType, Donation
from expenses.models import Expense, ExpenseCategory


@pytest.mark.django_db
class TestDonationWorkflow:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='donor', password='SecurePass123!@#', email='donor@test.com'
        )
        self.admin = User.objects.create_user(
            username='donadmin', password='AdminPass123!@#', email='donadmin@test.com'
        )
        from roles.models import UserRole
        role = UserRole.objects.get(user=self.admin)
        role.role = 'admin'
        role.approved = True
        role.save()

        self.donation_type = DonationType.objects.create(
            name='General Fund',
            desc='General donations',
            created_by=self.admin,
        )
        cache.clear()

    def test_add_donation_requires_login(self):
        response = self.client.get('/donation/add-donation/')
        assert response.status_code == 302
        assert '/auth/login' in response.url

    def test_add_donation_renders_form(self):
        self.client.login(username='donor', password='SecurePass123!@#')
        response = self.client.get('/donation/add-donation/')
        assert response.status_code == 200

    def test_add_donation_success(self):
        self.client.login(username='donor', password='SecurePass123!@#')
        response = self.client.post('/donation/add-donation/', {
            'donation_for': self.donation_type.id,
            'amount': 5000,
            'display_name': 'John Doe',
            'handover_by': 'Cash',
            'desc': 'Monthly contribution',
        })
        assert response.status_code == 302
        donation = Donation.objects.get(display_name='John Doe')
        assert donation.is_approved is False
        assert donation.add_by == self.user
        assert donation.amount == 5000

    def test_new_donation_not_visible_publicly(self):
        Donation.objects.create(
            add_by=self.user, donation_for=self.donation_type,
            amount=1000, display_name='Hidden', handover_by='X',
            is_approved=False
        )
        response = self.client.get(f'/donation/donation/{self.donation_type.id}')
        assert b'Hidden' not in response.content

    def test_approved_donation_visible_publicly(self):
        Donation.objects.create(
            add_by=self.user, donation_for=self.donation_type,
            amount=1000, display_name='Visible Donor', handover_by='X',
            is_approved=True
        )
        response = self.client.get(f'/donation/donation/{self.donation_type.id}')
        assert b'Visible Donor' in response.content

    def test_admin_can_approve_donation(self):
        donation = Donation.objects.create(
            add_by=self.user, donation_for=self.donation_type,
            amount=2000, display_name='Pending', handover_by='X',
            is_approved=False
        )
        self.client.login(username='donadmin', password='AdminPass123!@#')
        response = self.client.post(f'/donation/donations/{donation.id}/action/', {
            'action': 'approve',
        })
        assert response.status_code == 302
        donation.refresh_from_db()
        assert donation.is_approved is True

    def test_admin_can_reject_donation(self):
        donation = Donation.objects.create(
            add_by=self.user, donation_for=self.donation_type,
            amount=2000, display_name='Rejected', handover_by='X',
            is_approved=False
        )
        self.client.login(username='donadmin', password='AdminPass123!@#')
        response = self.client.post(f'/donation/donations/{donation.id}/action/', {
            'action': 'reject',
        })
        assert response.status_code == 302
        assert not Donation.objects.filter(id=donation.id).exists()

    def test_non_admin_cannot_access_admin_view(self):
        self.client.login(username='donor', password='SecurePass123!@#')
        response = self.client.get('/donation/donations/admin/')
        assert response.status_code == 302

    def test_donation_export_csv(self):
        Donation.objects.create(
            add_by=self.user, donation_for=self.donation_type,
            amount=3000, display_name='Export Test', handover_by='Bank',
            is_approved=True
        )
        self.client.login(username='donadmin', password='AdminPass123!@#')
        response = self.client.get('/donation/donations/admin/export/')
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']
        assert b'Export Test' in response.content


@pytest.mark.django_db
class TestExpenseWorkflow:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='expuser', password='SecurePass123!@#', email='exp@test.com'
        )
        self.admin = User.objects.create_user(
            username='expadmin', password='AdminPass123!@#', email='expadmin@test.com'
        )
        from roles.models import UserRole
        role = UserRole.objects.get(user=self.admin)
        role.role = 'admin'
        role.approved = True
        role.save()

        self.category = ExpenseCategory.objects.create(name='Travel', is_active=True)
        cache.clear()

    def test_expense_list_requires_login(self):
        response = self.client.get('/expenses/')
        assert response.status_code == 302

    def test_expense_list_renders(self):
        self.client.login(username='expuser', password='SecurePass123!@#')
        response = self.client.get('/expenses/')
        assert response.status_code == 200

    def test_create_expense_success(self):
        self.client.login(username='expuser', password='SecurePass123!@#')
        response = self.client.post('/expenses/create/', {
            'title': 'Taxi fare',
            'description': 'Airport transfer',
            'amount': '150.00',
            'category': self.category.id,
        })
        assert response.status_code == 302
        expense = Expense.objects.get(title='Taxi fare')
        assert expense.status == 'draft'
        assert expense.raised_by == self.user
        assert expense.amount == Decimal('150.00')

    def test_submit_expense_changes_status(self):
        self.client.login(username='expuser', password='SecurePass123!@#')
        expense = Expense.objects.create(
            raised_by=self.user, title='Test', description='Desc',
            amount=100, category=self.category, status='draft'
        )
        response = self.client.post(f'/expenses/{expense.id}/submit/')
        assert response.status_code == 302
        expense.refresh_from_db()
        assert expense.status == 'pending'

    def test_cannot_submit_others_expense(self):
        other = User.objects.create_user(username='other', password='OtherPass123!@#')
        expense = Expense.objects.create(
            raised_by=other, title='Other', description='Desc',
            amount=100, category=self.category, status='draft'
        )
        self.client.login(username='expuser', password='SecurePass123!@#')
        response = self.client.post(f'/expenses/{expense.id}/submit/')
        assert response.status_code == 404

    def test_admin_approve_expense(self):
        expense = Expense.objects.create(
            raised_by=self.user, title='Approve Me', description='Desc',
            amount=200, category=self.category, status='pending'
        )
        self.client.login(username='expadmin', password='AdminPass123!@#')
        response = self.client.post(f'/expenses/{expense.id}/action/', {
            'action': 'approve',
        })
        assert response.status_code == 302
        expense.refresh_from_db()
        assert expense.status == 'approved'
        assert expense.approved_by == self.admin

    def test_admin_reject_expense(self):
        expense = Expense.objects.create(
            raised_by=self.user, title='Reject Me', description='Desc',
            amount=200, category=self.category, status='pending'
        )
        self.client.login(username='expadmin', password='AdminPass123!@#')
        response = self.client.post(f'/expenses/{expense.id}/action/', {
            'action': 'reject',
            'reason': 'No receipt attached',
        })
        assert response.status_code == 302
        expense.refresh_from_db()
        assert expense.status == 'rejected'
        assert 'No receipt' in expense.rejection_reason

    def test_admin_mark_paid(self):
        expense = Expense.objects.create(
            raised_by=self.user, title='Pay Me', description='Desc',
            amount=300, category=self.category, status='approved'
        )
        self.client.login(username='expadmin', password='AdminPass123!@#')
        response = self.client.post(f'/expenses/{expense.id}/action/', {
            'action': 'mark_paid',
        })
        assert response.status_code == 302
        expense.refresh_from_db()
        assert expense.status == 'paid'

    def test_expense_export_csv(self):
        Expense.objects.create(
            raised_by=self.user, title='CSV Export', description='Desc',
            amount=500, category=self.category, status='paid'
        )
        self.client.login(username='expadmin', password='AdminPass123!@#')
        response = self.client.get('/expenses/admin/export/')
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']
        assert b'CSV Export' in response.content
