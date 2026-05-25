"""
Django management command to create load test users.

Usage:
    python manage.py create_loadtest_users
    python manage.py create_loadtest_users --cleanup
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


LOADTEST_USERS = [
    {"username": "loadtest_user", "password": "LoadTest_Pass123!", "role": "member"},
    {"username": "loadtest_admin", "password": "LoadTest_Admin123!", "role": "admin"},
]


class Command(BaseCommand):
    help = "Create or remove load test user accounts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cleanup", action="store_true",
            help="Remove load test users instead of creating them",
        )

    def handle(self, *args, **options):
        if options["cleanup"]:
            self._cleanup()
        else:
            self._create()

    def _create(self):
        from roles.services import RoleService

        for user_data in LOADTEST_USERS:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={"email": f"{user_data['username']}@loadtest.local"},
            )
            if created:
                user.set_password(user_data["password"])
                user.save()
                RoleService.assign_role(user, user_data["role"])
                self.stdout.write(self.style.SUCCESS(
                    f"Created {user_data['username']} (role={user_data['role']})"
                ))
            else:
                self.stdout.write(f"Already exists: {user_data['username']}")

    def _cleanup(self):
        usernames = [u["username"] for u in LOADTEST_USERS]
        deleted, _ = User.objects.filter(username__in=usernames).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} load test user(s)"))
