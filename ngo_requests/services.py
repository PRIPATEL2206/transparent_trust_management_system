from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from services.base import BaseService, service_error_handler
from services.exceptions import ValidationError, PermissionDeniedError
from approval_engine.services import ApprovalService
from roles.services import RoleService
from .models import FundRequest


class NGOFundService(BaseService):

    @staticmethod
    @service_error_handler
    def create_request(user: User, title: str, description: str,
                       amount: float, documents=None) -> FundRequest:
        if not RoleService.has_role(user, 'ngo'):
            raise PermissionDeniedError("Only NGO users can create fund requests")
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        fund_request = FundRequest.objects.create(
            ngo_user=user,
            title=title,
            description=description,
            amount_requested=amount,
            supporting_documents=documents,
        )
        ApprovalService.submit_for_approval(fund_request, user)
        NGOFundService.log_action('fund_request_created', user=user, request_id=fund_request.id)
        return fund_request

    @staticmethod
    @service_error_handler
    @transaction.atomic
    def approve_request(fund_request: FundRequest, admin_user: User,
                        amount_approved: float, notes: str = '') -> FundRequest:
        fund_request = FundRequest.objects.select_for_update().get(pk=fund_request.pk)
        if fund_request.status not in ('pending', 'under_review'):
            raise ValidationError("Request cannot be approved in current state")

        fund_request.status = 'approved'
        fund_request.amount_approved = amount_approved
        fund_request.reviewed_by = admin_user
        fund_request.review_notes = notes
        fund_request.save()

        NGOFundService.log_action('fund_request_approved', user=admin_user, request_id=fund_request.id)
        return fund_request

    @staticmethod
    @service_error_handler
    @transaction.atomic
    def reject_request(fund_request: FundRequest, admin_user: User, notes: str = '') -> FundRequest:
        fund_request = FundRequest.objects.select_for_update().get(pk=fund_request.pk)
        if fund_request.status not in ('pending', 'under_review'):
            raise ValidationError("Request cannot be rejected in current state")

        fund_request.status = 'rejected'
        fund_request.reviewed_by = admin_user
        fund_request.review_notes = notes
        fund_request.save()

        NGOFundService.log_action('fund_request_rejected', user=admin_user, request_id=fund_request.id)
        return fund_request

    @staticmethod
    @service_error_handler
    @transaction.atomic
    def mark_disbursed(fund_request: FundRequest, admin_user: User) -> FundRequest:
        fund_request = FundRequest.objects.select_for_update().get(pk=fund_request.pk)
        if fund_request.status != 'approved':
            raise ValidationError("Only approved requests can be marked as disbursed")

        fund_request.status = 'disbursed'
        fund_request.save()

        NGOFundService.log_action('fund_disbursed', user=admin_user, request_id=fund_request.id)
        return fund_request

    @staticmethod
    def get_ngo_requests(user: User):
        return FundRequest.objects.filter(ngo_user=user).order_by('-created_at')

    @staticmethod
    def get_pending_requests():
        return FundRequest.objects.filter(
            status__in=['pending', 'under_review']
        ).select_related('ngo_user').order_by('-created_at')
