import hashlib
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Create a backup of the SQLite database with integrity verification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir', type=str, default=None,
            help='Directory to save backup (default: <BASE_DIR>/backups/)'
        )
        parser.add_argument(
            '--verify', action='store_true',
            help='Verify backup integrity after creation'
        )
        parser.add_argument(
            '--keep', type=int, default=10,
            help='Number of recent backups to keep (default: 10)'
        )

    def handle(self, *args, **options):
        db_path = Path(settings.DATABASES['default']['NAME'])

        if not db_path.exists():
            self.stderr.write(self.style.ERROR(f'Database not found: {db_path}'))
            return

        output_dir = Path(options['output_dir']) if options['output_dir'] else settings.BASE_DIR / 'backups'
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'db_backup_{timestamp}.sqlite3'
        backup_path = output_dir / backup_name

        shutil.copy2(db_path, backup_path)

        size_mb = backup_path.stat().st_size / (1024 * 1024)
        checksum = self._file_checksum(backup_path)
        self.stdout.write(self.style.SUCCESS(
            f'Backup created: {backup_path} ({size_mb:.2f} MB)'
        ))
        self.stdout.write(f'  SHA256: {checksum}')

        if options['verify']:
            self._verify_backup(backup_path)

        keep = options['keep']
        backups = sorted(output_dir.glob('db_backup_*.sqlite3'), reverse=True)
        for old_backup in backups[keep:]:
            old_backup.unlink()
            self.stdout.write(f'  Removed old backup: {old_backup.name}')

    def _file_checksum(self, path):
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _verify_backup(self, backup_path):
        try:
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            cursor.execute('PRAGMA integrity_check')
            result = cursor.fetchone()
            conn.close()
            if result[0] == 'ok':
                self.stdout.write(self.style.SUCCESS('  Integrity check: PASSED'))
            else:
                self.stderr.write(self.style.ERROR(f'  Integrity check: FAILED - {result[0]}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'  Integrity check: ERROR - {e}'))
