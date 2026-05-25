from django.core.management.base import BaseCommand
from notices.services import NoticeService


class Command(BaseCommand):
    help = 'Deactivates expired notices'

    def handle(self, *args, **options):
        count = NoticeService.cleanup_expired()
        self.stdout.write(self.style.SUCCESS(f'Deactivated {count} expired notices.'))
