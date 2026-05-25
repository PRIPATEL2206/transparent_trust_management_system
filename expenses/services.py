from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from services.base import BaseService, service_error_handler
from services.exceptions import ValidationError, PermissionDeniedError
from approval_engine.services import ApprovalService
from .models import Expense


class ExpenseService(BaseService):

    @staticmethod
    @service_error_handler
    def create_expense(user: User, title: str, description: str, amount, category, receipt=None) -> Expense:
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        expense = Expense.objects.create(
            raised_by=user,
            title=title,
            description=description,
            amount=amount,
            category=category,
            receipt=receipt,
            status='draft'
        )
        ExpenseService.log_action('expense_created', user=user, expense_id=expense.id)
        return expense

    @staticmethod
    @service_error_handler
    def submit_for_approval(expense: Expense, user: User) -> Expense:
        if expense.raised_by != user:
            raise PermissionDeniedError("Only the creator can submit for approval")
        if expense.status != 'draft':
            raise ValidationError("Only draft expenses can be submitted")

        expense.status = 'pending'
        expense.save()
        ApprovalService.submit_for_approval(expense, user)
        ExpenseService.log_action('expense_submitted', user=user, expense_id=expense.id)
        return expense

    @staticmethod
    @service_error_handler
    @transaction.atomic
    def approve_expense(expense: Expense, admin_user: User) -> Expense:
        expense = Expense.objects.select_for_update().get(pk=expense.pk)
        if expense.status != 'pending':
            raise ValidationError("Only pending expenses can be approved")

        expense.status = 'approved'
        expense.approved_by = admin_user
        expense.approved_at = timezone.now()
        expense.save()
        ExpenseService.log_action('expense_approved', user=admin_user, expense_id=expense.id)
        return expense

    @staticmethod
    @service_error_handler
    @transaction.atomic
    def reject_expense(expense: Expense, admin_user: User, reason: str = '') -> Expense:
        expense = Expense.objects.select_for_update().get(pk=expense.pk)
        if expense.status != 'pending':
            raise ValidationError("Only pending expenses can be rejected")

        expense.status = 'rejected'
        expense.rejection_reason = reason
        expense.save()
        ExpenseService.log_action('expense_rejected', user=admin_user, expense_id=expense.id)
        return expense

    @staticmethod
    @service_error_handler
    @transaction.atomic
    def mark_paid(expense: Expense, admin_user: User) -> Expense:
        expense = Expense.objects.select_for_update().get(pk=expense.pk)
        if expense.status != 'approved':
            raise ValidationError("Only approved expenses can be marked as paid")

        expense.status = 'paid'
        expense.save()
        ExpenseService.log_action('expense_paid', user=admin_user, expense_id=expense.id)
        return expense

    @staticmethod
    def get_user_expenses(user: User):
        return Expense.objects.filter(raised_by=user).select_related('category').order_by('-created_at')

    @staticmethod
    def get_pending_expenses():
        return Expense.objects.filter(status='pending').select_related('raised_by', 'category')
