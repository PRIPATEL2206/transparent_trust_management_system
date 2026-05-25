from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from config_app.models import SiteConfig


class Command(BaseCommand):
    help = 'Initial project setup: creates site config, seeds roles, assigns super_admin to superusers'

    def add_arguments(self, parser):
        parser.add_argument('--create-admin', action='store_true', help='Create a default admin user (admin/admin123)')

    def handle(self, *args, **options):
        self.stdout.write('Setting up Trust Management System...\n')

        config = SiteConfig.get_instance()
        self.stdout.write(self.style.SUCCESS(f'[1/4] Site config ready: "{config.trust_name}"'))

        call_command('seed_roles')
        self.stdout.write(self.style.SUCCESS('[2/4] Roles seeded'))

        if options['create_admin'] and not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@trustmgmt.local',
                password='admin123'
            )
            from roles.models import UserRole
            UserRole.objects.filter(user=admin).update(role='super_admin', approved=True)
            self.stdout.write(self.style.SUCCESS('[3/4] Admin user created (admin/admin123)'))
        elif User.objects.filter(is_superuser=True).exists():
            from roles.models import UserRole
            for su in User.objects.filter(is_superuser=True):
                UserRole.objects.filter(user=su).update(role='super_admin', approved=True)
            self.stdout.write(self.style.SUCCESS('[3/4] Superusers assigned super_admin role'))
        else:
            self.stdout.write(self.style.WARNING(
                '[3/4] No superuser found. Run: python manage.py createsuperuser'
            ))

        call_command('cleanup_notices')
        self.stdout.write(self.style.SUCCESS('[4/4] Expired notices cleaned up'))

        self.stdout.write(self.style.SUCCESS('\nSetup complete! Run: python manage.py runserver'))
