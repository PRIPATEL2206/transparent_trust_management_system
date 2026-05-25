import uuid
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.files.base import ContentFile

from services.base import BaseService, service_error_handler
from services.exceptions import ValidationError, DuplicateError
from .models import Transaction, Receipt


class PaymentService(BaseService):

    @staticmethod
    @service_error_handler
    def initiate_payment(user: User, amount: Decimal, transaction_type: str,
                         idempotency_key: str = None, metadata: dict = None) -> Transaction:
        if amount <= 0:
            raise ValidationError("Payment amount must be positive")

        if idempotency_key is None:
            idempotency_key = str(uuid.uuid4())

        existing = Transaction.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            if existing.status == 'completed':
                return existing
            if existing.status == 'initiated':
                return existing
            raise DuplicateError("A payment with this key already exists and failed")

        transaction = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type=transaction_type,
            idempotency_key=idempotency_key,
            metadata=metadata or {}
        )
        PaymentService.log_action('payment_initiated', user=user, transaction_id=transaction.id)
        return transaction

    @staticmethod
    @service_error_handler
    def complete_payment(transaction_id: int, reference_id: str = '') -> Transaction:
        transaction = Transaction.objects.get(id=transaction_id)
        if transaction.status != 'initiated':
            raise ValidationError(f"Cannot complete transaction in '{transaction.status}' state")

        transaction.status = 'completed'
        transaction.reference_id = reference_id
        transaction.completed_at = timezone.now()
        transaction.save()

        PaymentService.log_action('payment_completed', user=transaction.user, transaction_id=transaction.id)
        return transaction

    @staticmethod
    @service_error_handler
    def fail_payment(transaction_id: int, reason: str = '') -> Transaction:
        transaction = Transaction.objects.get(id=transaction_id)
        transaction.status = 'failed'
        transaction.metadata['failure_reason'] = reason
        transaction.save()
        return transaction

    @staticmethod
    def get_user_transactions(user: User):
        return Transaction.objects.filter(user=user).order_by('-created_at')


class ReceiptService(BaseService):

    @staticmethod
    @service_error_handler
    @transaction.atomic
    def generate_receipt(transaction_obj: Transaction) -> Receipt:
        if transaction_obj.status != 'completed':
            raise ValidationError("Can only generate receipts for completed transactions")

        if hasattr(transaction_obj, 'receipt'):
            return transaction_obj.receipt

        receipt_number = ReceiptService.get_next_receipt_number()

        html_content = render_to_string('payments/receipt_template.html', {
            'transaction': transaction_obj,
            'receipt_number': receipt_number,
        })

        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
        except ImportError:
            pdf_bytes = html_content.encode('utf-8')

        receipt = Receipt(
            transaction=transaction_obj,
            receipt_number=receipt_number,
        )
        receipt.pdf_file.save(
            f'receipt_{receipt_number}.pdf',
            ContentFile(pdf_bytes),
            save=False
        )
        receipt.save()

        transaction_obj.receipt_generated = True
        transaction_obj.save()

        ReceiptService.log_action('receipt_generated', user=transaction_obj.user, receipt=receipt_number)
        return receipt

    @staticmethod
    @transaction.atomic
    def get_next_receipt_number() -> str:
        last = Receipt.objects.select_for_update().order_by('-id').first()
        if last:
            try:
                num = int(last.receipt_number.split('-')[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1
        return f"RCP-{num:06d}"
