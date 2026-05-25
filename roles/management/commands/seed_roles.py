from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from roles.models import UserRole, RolePermission
from roles.services import DEFAULT_PERMISSIONS


class Command(BaseCommand):
    help = 'Seeds default role permissions and assigns roles to existing users without one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all role permissions to defaults',
        )

    def handle(self, *args, **options):
        if options['reset']:
            RolePermission.objects.all().delete()
            self.stdout.write('Cleared existing role permissions.')

        created_count = 0
        for role, permissions in DEFAULT_PERMISSIONS.items():
            for perm in permissions:
                _, created = RolePermission.objects.get_or_create(
                    role=role,
                    permission=perm,
                    defaults={'description': f'{perm} for {role}'}
                )
                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created_count} role permissions.'))

        users_without_role = User.objects.filter(role_profile__isnull=True)
        role_count = 0
        for user in users_without_role:
            UserRole.objects.create(user=user, role='user', approved=True)
            role_count += 1

        if role_count:
            self.stdout.write(self.style.SUCCESS(f'Assigned "user" role to {role_count} existing users.'))

        first_superuser = User.objects.filter(is_superuser=True).first()
        if first_superuser:
            role, _ = UserRole.objects.get_or_create(user=first_superuser)
            if role.role != 'super_admin':
                role.role = 'super_admin'
                role.approved = True
                role.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Assigned "super_admin" role to superuser: {first_superuser.username}'
                ))

        self.stdout.write(self.style.SUCCESS('Role seeding complete.'))
