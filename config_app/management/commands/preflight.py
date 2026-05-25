from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from pathlib import Path


class Command(BaseCommand):
    help = 'Run preflight checks to verify the system is properly configured'

    def handle(self, *args, **options):
        self.stdout.write('Running preflight checks...\n')
        errors = []

        # 1. Database connectivity
        try:
            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS('[PASS] Database connected'))
        except Exception as e:
            errors.append(f'Database: {e}')
            self.stdout.write(self.style.ERROR(f'[FAIL] Database: {e}'))

        # 2. Required directories
        required_dirs = ['media', 'logs', 'static']
        for d in required_dirs:
            path = settings.BASE_DIR / d
            if path.exists():
                self.stdout.write(self.style.SUCCESS(f'[PASS] Directory exists: {d}/'))
            else:
                errors.append(f'Missing directory: {d}/')
                self.stdout.write(self.style.ERROR(f'[FAIL] Missing directory: {d}/'))

        # 3. SiteConfig exists
        try:
            from config_app.models import SiteConfig
            config = SiteConfig.get_instance()
            self.stdout.write(self.style.SUCCESS(f'[PASS] SiteConfig: "{config.trust_name}"'))
        except Exception as e:
            errors.append(f'SiteConfig: {e}')
            self.stdout.write(self.style.ERROR(f'[FAIL] SiteConfig: {e}'))

        # 4. Roles seeded
        try:
            from roles.models import RolePermission
            count = RolePermission.objects.count()
            if count > 0:
                self.stdout.write(self.style.SUCCESS(f'[PASS] Roles seeded ({count} permissions)'))
            else:
                errors.append('No role permissions found')
                self.stdout.write(self.style.WARNING('[WARN] No role permissions - run: manage.py seed_roles'))
        except Exception as e:
            errors.append(f'Roles: {e}')
            self.stdout.write(self.style.ERROR(f'[FAIL] Roles: {e}'))

        # 5. At least one superuser exists
        from django.contrib.auth.models import User
        superuser_count = User.objects.filter(is_superuser=True).count()
        if superuser_count > 0:
            self.stdout.write(self.style.SUCCESS(f'[PASS] Superuser exists ({superuser_count})'))
        else:
            errors.append('No superuser')
            self.stdout.write(self.style.WARNING('[WARN] No superuser - run: manage.py createsuperuser'))

        # 6. Static files
        static_root = Path(settings.STATIC_ROOT)
        if static_root.exists() and any(static_root.iterdir()):
            self.stdout.write(self.style.SUCCESS('[PASS] Static files collected'))
        else:
            self.stdout.write(self.style.WARNING('[WARN] Static files not collected - run: manage.py collectstatic'))

        # 7. Secret key safety
        if 'insecure' in settings.SECRET_KEY:
            errors.append('Insecure SECRET_KEY in use')
            self.stdout.write(self.style.WARNING('[WARN] Using insecure SECRET_KEY - set DJANGO_SECRET_KEY env var'))
        else:
            self.stdout.write(self.style.SUCCESS('[PASS] SECRET_KEY is custom'))

        # Summary
        self.stdout.write('')
        if errors:
            self.stdout.write(self.style.WARNING(f'Preflight complete: {len(errors)} issue(s) found'))
        else:
            self.stdout.write(self.style.SUCCESS('Preflight complete: All checks passed!'))
