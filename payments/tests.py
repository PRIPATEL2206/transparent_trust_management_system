from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User

from .models import Transaction, Receipt
from .services import PaymentService, ReceiptService
from services.exceptions import ValidationError, DuplicateError


class PaymentServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='payer', password='testpass')

    def test_initiate_payment(self):
        tx = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='donation',
            idempotency_key='key-001'
        )
        self.assertEqual(tx.status, 'initiated')
        self.assertEqual(tx.amount, Decimal('100.00'))
        self.assertEqual(tx.transaction_type, 'donation')
        self.assertEqual(tx.idempotency_key, 'key-001')

    def test_initiate_payment_generates_key(self):
        tx = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('50.00'),
            transaction_type='fee'
        )
        self.assertIsNotNone(tx.idempotency_key)
        self.assertEqual(len(tx.idempotency_key), 36)

    def test_initiate_payment_negative_amount_raises(self):
        with self.assertRaises(Exception):
            PaymentService.initiate_payment(
                user=self.user,
                amount=Decimal('-10.00'),
                transaction_type='donation',
                idempotency_key='key-neg'
            )

    def test_initiate_payment_zero_amount_raises(self):
        with self.assertRaises(Exception):
            PaymentService.initiate_payment(
                user=self.user,
                amount=Decimal('0'),
                transaction_type='donation',
                idempotency_key='key-zero'
            )

    def test_idempotency_returns_existing_initiated(self):
        tx1 = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='donation',
            idempotency_key='key-idem'
        )
        tx2 = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='donation',
            idempotency_key='key-idem'
        )
        self.assertEqual(tx1.id, tx2.id)

    def test_idempotency_returns_existing_completed(self):
        tx = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='donation',
            idempotency_key='key-comp'
        )
        PaymentService.complete_payment(tx.id)
        tx2 = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='donation',
            idempotency_key='key-comp'
        )
        self.assertEqual(tx.id, tx2.id)

    def test_idempotency_failed_raises(self):
        tx = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='donation',
            idempotency_key='key-fail'
        )
        PaymentService.fail_payment(tx.id, reason='Insufficient funds')
        with self.assertRaises(Exception):
            PaymentService.initiate_payment(
                user=self.user,
                amount=Decimal('100.00'),
                transaction_type='donation',
                idempotency_key='key-fail'
            )

    def test_complete_payment(self):
        tx = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('200.00'),
            transaction_type='membership',
            idempotency_key='key-complete'
        )
        result = PaymentService.complete_payment(tx.id, reference_id='REF-123')
        self.assertEqual(result.status, 'completed')
        self.assertEqual(result.reference_id, 'REF-123')
        self.assertIsNotNone(result.completed_at)

    def test_complete_already_completed_raises(self):
        tx = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='donation',
            idempotency_key='key-double-complete'
        )
        PaymentService.complete_payment(tx.id)
        with self.assertRaises(Exception):
            PaymentService.complete_payment(tx.id)

    def test_fail_payment(self):
        tx = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('75.00'),
            transaction_type='fee',
            idempotency_key='key-to-fail'
        )
        result = PaymentService.fail_payment(tx.id, reason='Card declined')
        self.assertEqual(result.status, 'failed')
        self.assertEqual(result.metadata['failure_reason'], 'Card declined')

    def test_get_user_transactions(self):
        PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='donation',
            idempotency_key='key-list-1'
        )
        PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('200.00'),
            transaction_type='fee',
            idempotency_key='key-list-2'
        )
        txs = PaymentService.get_user_transactions(self.user)
        self.assertEqual(txs.count(), 2)

    def test_metadata_stored(self):
        tx = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('500.00'),
            transaction_type='donation',
            idempotency_key='key-meta',
            metadata={'campaign': 'flood-relief', 'note': 'Annual'}
        )
        self.assertEqual(tx.metadata['campaign'], 'flood-relief')


class ReceiptServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='receipter', password='testpass')

    def test_get_next_receipt_number_first(self):
        number = ReceiptService.get_next_receipt_number()
        self.assertEqual(number, 'RCP-000001')

    def test_get_next_receipt_number_increments(self):
        tx = PaymentService.initiate_payment(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='donation',
            idempotency_key='key-rcpt-1'
        )
        PaymentService.complete_payment(tx.id)
        Receipt.objects.create(
            transaction=tx,
            receipt_number='RCP-000001',
            pdf_file='receipts/test.pdf'
        )
        number = ReceiptService.get_next_receipt_number()
        self.assertEqual(number, 'RCP-000002')
