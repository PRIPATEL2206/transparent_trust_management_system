from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone

from services.base import BaseService, service_error_handler
from services.exceptions import ValidationError, PermissionDeniedError
from approval_engine.services import ApprovalService
from .models import Notice, Notification


class NotificationService(BaseService):

    @staticmethod
    def send(recipient, title, message, notification_type='info', link=''):
        Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
        )
        cache.delete(f'unread_notif_count:{recipient.id}')

    @staticmethod
    def get_unread(user):
        return Notification.objects.filter(recipient=user, is_read=False)

    @staticmethod
    def get_unread_count(user):
        return Notification.objects.filter(recipient=user, is_read=False).count()

    @staticmethod
    def mark_read(notification_id, user):
        Notification.objects.filter(id=notification_id, recipient=user).update(is_read=True)
        cache.delete(f'unread_notif_count:{user.id}')

    @staticmethod
    def mark_all_read(user):
        Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
        cache.delete(f'unread_notif_count:{user.id}')


class NoticeService(BaseService):

    @staticmethod
    @service_error_handler
    def create_notice(user: User, title: str, content: str, priority: str = 'medium',
                      expires_at=None) -> Notice:
        notice = Notice.objects.create(
            title=title,
            content=content,
            created_by=user,
            priority=priority,
            expires_at=expires_at,
            is_approved=False
        )
        ApprovalService.submit_for_approval(notice, user)
        NoticeService.log_action('notice_created', user=user, notice_id=notice.id)
        return notice

    @staticmethod
    @service_error_handler
    def approve_notice(notice: Notice, admin_user: User) -> Notice:
        notice.is_approved = True
        notice.save()
        NoticeService.log_action('notice_approved', user=admin_user, notice_id=notice.id)
        return notice

    @staticmethod
    @service_error_handler
    def deactivate_notice(notice: Notice, user: User) -> Notice:
        notice.is_active = False
        notice.save()
        NoticeService.log_action('notice_deactivated', user=user, notice_id=notice.id)
        return notice

    @staticmethod
    def get_active_notices():
        return Notice.objects.active().select_related('created_by')

    @staticmethod
    def get_pending_notices():
        return Notice.objects.filter(is_approved=False, is_active=True).select_related('created_by').order_by('-created_at')

    @staticmethod
    def cleanup_expired():
        expired = Notice.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        )
        count = expired.update(is_active=False)
        return count
