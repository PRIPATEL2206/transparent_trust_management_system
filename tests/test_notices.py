import pytest
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client
from django.utils import timezone

from notices.models import Notice, Notification
from notices.services import NoticeService, NotificationService
from roles.models import UserRole


@pytest.mark.django_db
class TestNoticeService:

    def setup_method(self):
        self.user = User.objects.create_user(
            username='noticeuser', password='SecurePass123!@#'
        )
        self.admin = User.objects.create_user(
            username='noticeadmin', password='AdminPass123!@#'
        )
        role = UserRole.objects.get(user=self.admin)
        role.role = 'admin'
        role.approved = True
        role.save()
        cache.clear()

    def test_create_notice(self):
        notice = NoticeService.create_notice(
            self.user, 'Test Notice', 'Some content', priority='high'
        )
        assert notice.title == 'Test Notice'
        assert notice.is_approved is False
        assert notice.priority == 'high'
        assert notice.created_by == self.user

    def test_approve_notice(self):
        notice = NoticeService.create_notice(
            self.user, 'Approve Me', 'Content'
        )
        NoticeService.approve_notice(notice, self.admin)
        notice.refresh_from_db()
        assert notice.is_approved is True

    def test_deactivate_notice(self):
        notice = NoticeService.create_notice(
            self.user, 'Deactivate', 'Content'
        )
        notice.is_approved = True
        notice.save()
        NoticeService.deactivate_notice(notice, self.admin)
        notice.refresh_from_db()
        assert notice.is_active is False

    def test_get_active_notices_excludes_unapproved(self):
        NoticeService.create_notice(self.user, 'Pending', 'Content')
        Notice.objects.create(
            title='Approved', content='OK',
            created_by=self.user, is_approved=True
        )
        active = NoticeService.get_active_notices()
        assert active.count() == 1
        assert active.first().title == 'Approved'

    def test_get_active_notices_excludes_expired(self):
        Notice.objects.create(
            title='Expired', content='Old',
            created_by=self.user, is_approved=True,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        Notice.objects.create(
            title='Fresh', content='New',
            created_by=self.user, is_approved=True,
            expires_at=timezone.now() + timedelta(days=1)
        )
        active = NoticeService.get_active_notices()
        assert active.count() == 1
        assert active.first().title == 'Fresh'

    def test_cleanup_expired(self):
        Notice.objects.create(
            title='Should Expire', content='Old',
            created_by=self.user, is_approved=True, is_active=True,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        count = NoticeService.cleanup_expired()
        assert count == 1


@pytest.mark.django_db
class TestNotificationService:

    def setup_method(self):
        self.user = User.objects.create_user(
            username='notifuser', password='SecurePass123!@#'
        )
        cache.clear()

    def test_send_notification(self):
        NotificationService.send(
            self.user, 'Welcome', 'You joined!',
            notification_type='success', link='/home/'
        )
        notif = Notification.objects.get(recipient=self.user)
        assert notif.title == 'Welcome'
        assert notif.is_read is False
        assert notif.link == '/home/'

    def test_get_unread(self):
        NotificationService.send(self.user, 'Unread', 'msg')
        NotificationService.send(self.user, 'Also Unread', 'msg2')
        unread = NotificationService.get_unread(self.user)
        assert unread.count() == 2

    def test_get_unread_count(self):
        NotificationService.send(self.user, 'One', 'msg')
        NotificationService.send(self.user, 'Two', 'msg')
        assert NotificationService.get_unread_count(self.user) == 2

    def test_mark_read(self):
        NotificationService.send(self.user, 'Read Me', 'msg')
        notif = Notification.objects.get(title='Read Me')
        NotificationService.mark_read(notif.id, self.user)
        notif.refresh_from_db()
        assert notif.is_read is True

    def test_mark_all_read(self):
        NotificationService.send(self.user, 'A', 'msg')
        NotificationService.send(self.user, 'B', 'msg')
        NotificationService.mark_all_read(self.user)
        assert NotificationService.get_unread_count(self.user) == 0

    def test_mark_read_wrong_user_no_effect(self):
        other = User.objects.create_user(username='other', password='OtherPass123!@#')
        NotificationService.send(self.user, 'Mine', 'msg')
        notif = Notification.objects.get(title='Mine')
        NotificationService.mark_read(notif.id, other)
        notif.refresh_from_db()
        assert notif.is_read is False


@pytest.mark.django_db
class TestNoticeViews:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nvuser', password='SecurePass123!@#'
        )
        self.admin = User.objects.create_user(
            username='nvadmin', password='AdminPass123!@#'
        )
        role = UserRole.objects.get(user=self.admin)
        role.role = 'admin'
        role.approved = True
        role.save()
        cache.clear()

    def test_notice_list_public(self):
        response = self.client.get('/notices/')
        assert response.status_code == 200

    def test_notice_create_requires_member_role(self):
        self.client.login(username='nvuser', password='SecurePass123!@#')
        response = self.client.get('/notices/create/')
        assert response.status_code == 302

    def test_notice_create_allowed_for_member(self):
        role = UserRole.objects.get(user=self.user)
        role.role = 'member'
        role.approved = True
        role.save()
        self.client.login(username='nvuser', password='SecurePass123!@#')
        response = self.client.get('/notices/create/')
        assert response.status_code == 200

    def test_notice_admin_requires_admin(self):
        self.client.login(username='nvuser', password='SecurePass123!@#')
        response = self.client.get('/notices/admin/')
        assert response.status_code == 302

    def test_notifications_page_requires_login(self):
        response = self.client.get('/notices/notifications/')
        assert response.status_code == 302

    def test_notifications_page_renders(self):
        self.client.login(username='nvuser', password='SecurePass123!@#')
        response = self.client.get('/notices/notifications/')
        assert response.status_code == 200
