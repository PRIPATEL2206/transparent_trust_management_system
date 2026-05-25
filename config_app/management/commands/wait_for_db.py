import time
import sys
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Wait for the database to become available'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout', type=int, default=30,
            help='Maximum seconds to wait (default: 30)'
        )
        parser.add_argument(
            '--interval', type=float, default=1.0,
            help='Seconds between retries (default: 1.0)'
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        interval = options['interval']
        start = time.time()

        self.stdout.write('Waiting for database...')

        while True:
            try:
                connection = connections['default']
                connection.ensure_connection()
                self.stdout.write(self.style.SUCCESS(
                    f'Database available after {time.time() - start:.1f}s'
                ))
                return
            except OperationalError:
                elapsed = time.time() - start
                if elapsed >= timeout:
                    self.stderr.write(self.style.ERROR(
                        f'Database unavailable after {timeout}s — giving up'
                    ))
                    sys.exit(1)
                time.sleep(interval)
