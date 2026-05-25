import pytest
import uuid
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client

from payments.models import Transaction, Receipt
from payments.services import PaymentService, ReceiptService


@pytest.mark.django_db
class TestPaymentService:

    def setup_method(self):
        self.user = User.objects.create_user(
            username='payuser', password='SecurePass123!@#', email='pay@test.com'
        )
        cache.clear()

    def test_initiate_payment_creates_transaction(self):
        txn = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('500.00'),
            transaction_type='donation',
            idempotency_key='key-001'
        )
        assert txn.id is not None
        assert txn.status == 'initiated'
        assert txn.amount == Decimal('500.00')
        assert txn.user == self.user

    def test_initiate_payment_with_metadata(self):
        txn = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='fee',
            idempotency_key='key-meta',
            metadata={'notes': 'Monthly fee'}
        )
        assert txn.metadata == {'notes': 'Monthly fee'}

    def test_idempotency_returns_existing_transaction(self):
        key = 'idempotent-key-123'
        txn1 = PaymentService.initiate_payment(
            user=self.user, amount=Decimal('200.00'),
            transaction_type='membership', idempotency_key=key
        )
        txn2 = PaymentService.initiate_payment(
            user=self.user, amount=Decimal('200.00'),
            transaction_type='membership', idempotency_key=key
        )
        assert txn1.id == txn2.id

    def test_complete_payment(self):
        txn = PaymentService.initiate_payment(
            user=self.user, amount=Decimal('300.00'),
            transaction_type='donation', idempotency_key='complete-key'
        )
        completed = PaymentService.complete_payment(txn.id, reference_id='REF-EXT-001')
        assert completed.status == 'completed'
        assert completed.reference_id == 'REF-EXT-001'
        assert completed.completed_at is not None

    def test_fail_payment(self):
        txn = PaymentService.initiate_payment(
            user=self.user, amount=Decimal('50.00'),
            transaction_type='fee', idempotency_key='fail-key'
        )
        failed = PaymentService.fail_payment(txn.id, reason='Card declined')
        assert failed.status == 'failed'
        assert failed.metadata.get('failure_reason') == 'Card declined'

    def test_get_user_transactions(self):
        for i in range(3):
            PaymentService.initiate_payment(
                user=self.user, amount=Decimal('10.00'),
                transaction_type='fee', idempotency_key=f'list-key-{i}'
            )
        txns = PaymentService.get_user_transactions(self.user)
        assert txns.count() == 3

    def test_get_user_transactions_ordered_by_created_desc(self):
        t1 = PaymentService.initiate_payment(
            user=self.user, amount=Decimal('10.00'),
            transaction_type='fee', idempotency_key='order-1'
        )
        t2 = PaymentService.initiate_payment(
            user=self.user, amount=Decimal('20.00'),
            transaction_type='fee', idempotency_key='order-2'
        )
        txns = list(PaymentService.get_user_transactions(self.user))
        assert txns[0].id == t2.id

    def test_initiate_payment_generates_idempotency_key_if_none(self):
        txn = PaymentService.initiate_payment(
            user=self.user, amount=Decimal('100.00'),
            transaction_type='donation'
        )
        assert txn.idempotency_key is not None
        assert len(txn.idempotency_key) > 0


@pytest.mark.django_db
class TestReceiptService:

    def setup_method(self):
        self.user = User.objects.create_user(
            username='rcptuser', password='SecurePass123!@#', email='rcpt@test.com'
        )
        self.transaction = Transaction.objects.create(
            user=self.user, amount=Decimal('500.00'),
            transaction_type='donation', status='completed',
            idempotency_key=str(uuid.uuid4())
        )
        cache.clear()

    def test_get_next_receipt_number_format(self):
        num = ReceiptService.get_next_receipt_number()
        assert num.startswith('RCP-')
        assert len(num) == 10  # RCP-000001

    def test_get_next_receipt_number_increments(self):
        n1 = ReceiptService.get_next_receipt_number()
        Receipt.objects.create(
            transaction=self.transaction,
            receipt_number=n1,
            pdf_file=''
        )
        txn2 = Transaction.objects.create(
            user=self.user, amount=Decimal('100.00'),
            transaction_type='fee', status='completed',
            idempotency_key=str(uuid.uuid4())
        )
        n2 = ReceiptService.get_next_receipt_number()
        num1 = int(n1.split('-')[1])
        num2 = int(n2.split('-')[1])
        assert num2 == num1 + 1

    def test_generate_receipt_creates_receipt_object(self):
        receipt = ReceiptService.generate_receipt(self.transaction)
        assert receipt is not None
        assert receipt.receipt_number.startswith('RCP-')
        self.transaction.refresh_from_db()
        assert self.transaction.receipt_generated is True


@pytest.mark.django_db
class TestPaymentViews:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='pvuser', password='SecurePass123!@#', email='pv@test.com'
        )
        self.admin = User.objects.create_user(
            username='pvadmin', password='AdminPass123!@#', email='pvadmin@test.com'
        )
        from roles.models import UserRole
        role = UserRole.objects.get(user=self.admin)
        role.role = 'admin'
        role.approved = True
        role.save()
        cache.clear()

    def test_payment_history_requires_login(self):
        response = self.client.get('/payments/history/')
        assert response.status_code == 302
        assert '/auth/login' in response.url

    def test_payment_history_renders(self):
        self.client.login(username='pvuser', password='SecurePass123!@#')
        response = self.client.get('/payments/history/')
        assert response.status_code == 200

    def test_payment_admin_requires_admin(self):
        self.client.login(username='pvuser', password='SecurePass123!@#')
        response = self.client.get('/payments/admin/')
        assert response.status_code == 302

    def test_payment_admin_allowed_for_admin(self):
        self.client.login(username='pvadmin', password='AdminPass123!@#')
        response = self.client.get('/payments/admin/')
        assert response.status_code == 200

    def test_payment_export_csv(self):
        Transaction.objects.create(
            user=self.user, amount=Decimal('100.00'),
            transaction_type='donation', status='completed',
            idempotency_key=str(uuid.uuid4())
        )
        self.client.login(username='pvadmin', password='AdminPass123!@#')
        response = self.client.get('/payments/admin/export/')
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']
