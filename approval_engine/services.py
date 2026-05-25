from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.utils import timezone

from services.base import BaseService, service_error_handler
from services.exceptions import NotFoundError, ValidationError, PermissionDeniedError
from .models import ApprovalRequest


class ApprovalService(BaseService):

    @staticmethod
    @service_error_handler
    def submit_for_approval(instance, requested_by: User) -> ApprovalRequest:
        content_type = ContentType.objects.get_for_model(instance)

        existing = ApprovalRequest.objects.filter(
            content_type=content_type,
            object_id=instance.pk,
            status='pending'
        ).first()

        if existing:
            return existing

        approval = ApprovalRequest.objects.create(
            content_type=content_type,
            object_id=instance.pk,
            requested_by=requested_by,
            status='pending'
        )

        ApprovalService.log_action(
            'approval_submitted',
            user=requested_by,
            model=content_type.model,
            object_id=instance.pk
        )
        return approval

    @staticmethod
    @service_error_handler
    def approve(request_id: int, reviewed_by: User, notes: str = '') -> ApprovalRequest:
        try:
            approval = ApprovalRequest.objects.get(id=request_id)
        except ApprovalRequest.DoesNotExist:
            raise NotFoundError("Approval request not found")

        if not approval.is_pending:
            raise ValidationError("This request has already been processed")

        if approval.requested_by == reviewed_by:
            raise PermissionDeniedError("Cannot approve your own request")

        approval.status = 'approved'
        approval.reviewed_by = reviewed_by
        approval.reviewed_at = timezone.now()
        approval.notes = notes
        approval.save()

        ApprovalService.log_action(
            'approval_approved',
            user=reviewed_by,
            request_id=request_id
        )

        from services.audit import log_approval_action
        log_approval_action('approved', reviewed_by, approval)
        return approval

    @staticmethod
    @service_error_handler
    def reject(request_id: int, reviewed_by: User, notes: str = '') -> ApprovalRequest:
        try:
            approval = ApprovalRequest.objects.get(id=request_id)
        except ApprovalRequest.DoesNotExist:
            raise NotFoundError("Approval request not found")

        if not approval.is_pending:
            raise ValidationError("This request has already been processed")

        approval.status = 'rejected'
        approval.reviewed_by = reviewed_by
        approval.reviewed_at = timezone.now()
        approval.notes = notes
        approval.save()

        ApprovalService.log_action(
            'approval_rejected',
            user=reviewed_by,
            request_id=request_id
        )

        from services.audit import log_approval_action
        log_approval_action('rejected', reviewed_by, approval)
        return approval

    @staticmethod
    def get_pending(content_type_model: str = None) -> QuerySet:
        qs = ApprovalRequest.objects.filter(status='pending')
        if content_type_model:
            ct = ContentType.objects.get(model=content_type_model)
            qs = qs.filter(content_type=ct)
        return qs.select_related('requested_by', 'content_type').order_by('-created_at')

    @staticmethod
    def is_approved(instance) -> bool:
        content_type = ContentType.objects.get_for_model(instance)
        return ApprovalRequest.objects.filter(
            content_type=content_type,
            object_id=instance.pk,
            status='approved'
        ).exists()

    @staticmethod
    def get_for_object(instance) -> QuerySet:
        content_type = ContentType.objects.get_for_model(instance)
        return ApprovalRequest.objects.filter(
            content_type=content_type,
            object_id=instance.pk
        )
