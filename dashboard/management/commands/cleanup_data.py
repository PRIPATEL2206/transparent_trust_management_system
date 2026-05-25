from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Clean up old data: sessions, notifications, activity logs, expired notices, old reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=90,
            help='Delete records older than N days (default: 90)'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be deleted without deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff = timezone.now() - timedelta(days=days)
        total_deleted = 0

        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN - nothing will be deleted'))

        self.stdout.write(f'Cleaning up records older than {days} days (before {cutoff.date()})...\n')

        # 0. Expired sessions
        from django.contrib.sessions.models import Session
        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
        count = expired_sessions.count()
        if not dry_run:
            expired_sessions.delete()
        total_deleted += count
        self.stdout.write(self.style.SUCCESS(f'  Expired sessions: {count} deleted'))

        # 1. Old read notifications
        from notices.models import Notification
        old_notifications = Notification.objects.filter(
            is_read=True, created_at__lt=cutoff
        )
        count = old_notifications.count()
        if not dry_run:
            old_notifications.delete()
        total_deleted += count
        self.stdout.write(self.style.SUCCESS(f'  Notifications (read): {count} deleted'))

        # 2. Old activity logs
        from dashboard.models import ActivityLog
        old_logs = ActivityLog.objects.filter(created_at__lt=cutoff)
        count = old_logs.count()
        if not dry_run:
            old_logs.delete()
        total_deleted += count
        self.stdout.write(self.style.SUCCESS(f'  Activity logs: {count} deleted'))

        # 3. Expired and inactive notices
        from notices.models import Notice
        expired_notices = Notice.objects.filter(
            expires_at__lt=cutoff, is_active=False
        )
        count = expired_notices.count()
        if not dry_run:
            expired_notices.delete()
        total_deleted += count
        self.stdout.write(self.style.SUCCESS(f'  Expired notices: {count} deleted'))

        # 4. Old generated reports
        from reports.models import GeneratedReport
        old_reports = GeneratedReport.objects.filter(created_at__lt=cutoff)
        count = old_reports.count()
        if not dry_run:
            old_reports.delete()
        total_deleted += count
        self.stdout.write(self.style.SUCCESS(f'  Old reports: {count} deleted'))

        self.stdout.write(self.style.SUCCESS(f'\nCleanup complete. Total records removed: {total_deleted}'))
