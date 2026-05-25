import pytest
from django.contrib.auth.models import User
from django.core.cache import cache

from approval_engine.models import ApprovalRequest
from approval_engine.services import ApprovalService
from expenses.models import Expense, ExpenseCategory
from notices.models import Notice
from services.exceptions import ValidationError, PermissionDeniedError, NotFoundError


@pytest.mark.django_db
class TestApprovalService:

    def setup_method(self):
        self.requester = User.objects.create_user(
            username='requester', password='SecurePass123!@#'
        )
        self.reviewer = User.objects.create_user(
            username='reviewer', password='SecurePass123!@#'
        )
        self.category = ExpenseCategory.objects.create(name='Office', is_active=True)
        self.expense = Expense.objects.create(
            raised_by=self.requester, title='Office supplies',
            description='Pens and paper', amount=50,
            category=self.category, status='pending'
        )
        cache.clear()

    def test_submit_for_approval_creates_request(self):
        approval = ApprovalService.submit_for_approval(self.expense, self.requester)
        assert approval is not None
        assert approval.status == 'pending'
        assert approval.requested_by == self.requester

    def test_submit_duplicate_returns_existing(self):
        first = ApprovalService.submit_for_approval(self.expense, self.requester)
        second = ApprovalService.submit_for_approval(self.expense, self.requester)
        assert first.id == second.id

    def test_approve_success(self):
        approval = ApprovalService.submit_for_approval(self.expense, self.requester)
        result = ApprovalService.approve(approval.id, self.reviewer, notes='Looks good')
        assert result.status == 'approved'
        assert result.reviewed_by == self.reviewer
        assert result.reviewed_at is not None
        assert result.notes == 'Looks good'

    def test_reject_success(self):
        approval = ApprovalService.submit_for_approval(self.expense, self.requester)
        result = ApprovalService.reject(approval.id, self.reviewer, notes='Missing receipt')
        assert result.status == 'rejected'
        assert result.reviewed_by == self.reviewer

    def test_cannot_approve_own_request(self):
        approval = ApprovalService.submit_for_approval(self.expense, self.requester)
        with pytest.raises(PermissionDeniedError):
            ApprovalService.approve(approval.id, self.requester)

    def test_cannot_approve_already_processed(self):
        approval = ApprovalService.submit_for_approval(self.expense, self.requester)
        ApprovalService.approve(approval.id, self.reviewer)
        with pytest.raises(ValidationError):
            ApprovalService.approve(approval.id, self.reviewer)

    def test_cannot_reject_already_processed(self):
        approval = ApprovalService.submit_for_approval(self.expense, self.requester)
        ApprovalService.reject(approval.id, self.reviewer)
        with pytest.raises(ValidationError):
            ApprovalService.reject(approval.id, self.reviewer)

    def test_approve_nonexistent_raises_not_found(self):
        with pytest.raises(NotFoundError):
            ApprovalService.approve(99999, self.reviewer)

    def test_is_approved_true_after_approval(self):
        approval = ApprovalService.submit_for_approval(self.expense, self.requester)
        ApprovalService.approve(approval.id, self.reviewer)
        assert ApprovalService.is_approved(self.expense) is True

    def test_is_approved_false_when_pending(self):
        ApprovalService.submit_for_approval(self.expense, self.requester)
        assert ApprovalService.is_approved(self.expense) is False

    def test_get_pending_returns_only_pending(self):
        ApprovalService.submit_for_approval(self.expense, self.requester)

        expense2 = Expense.objects.create(
            raised_by=self.requester, title='Approved already',
            description='Done', amount=100, category=self.category, status='pending'
        )
        approval2 = ApprovalService.submit_for_approval(expense2, self.requester)
        ApprovalService.approve(approval2.id, self.reviewer)

        pending = ApprovalService.get_pending()
        assert pending.count() == 1

    def test_get_pending_filters_by_content_type(self):
        ApprovalService.submit_for_approval(self.expense, self.requester)

        notice = Notice.objects.create(
            title='Test Notice', content='Content',
            created_by=self.requester, priority='medium'
        )
        ApprovalService.submit_for_approval(notice, self.requester)

        expense_pending = ApprovalService.get_pending(content_type_model='expense')
        assert expense_pending.count() == 1

    def test_get_for_object_returns_all_history(self):
        approval = ApprovalService.submit_for_approval(self.expense, self.requester)
        ApprovalService.reject(approval.id, self.reviewer, notes='First try')

        self.expense.status = 'pending'
        self.expense.save()
        ApprovalRequest.objects.filter(id=approval.id).update(status='rejected')

        approval2 = ApprovalRequest.objects.create(
            content_type=approval.content_type,
            object_id=self.expense.pk,
            requested_by=self.requester,
            status='pending'
        )

        history = ApprovalService.get_for_object(self.expense)
        assert history.count() == 2
