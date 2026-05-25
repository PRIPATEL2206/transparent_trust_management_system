from django.db import migrations


def assign_roles_to_existing_users(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserRole = apps.get_model('roles', 'UserRole')

    for user in User.objects.all():
        if not UserRole.objects.filter(user=user).exists():
            role = 'super_admin' if user.is_superuser else 'user'
            UserRole.objects.create(
                user=user,
                role=role,
                approved=True,
            )


def reverse_migration(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0001_initial'),
        ('auth', '__latest__'),
    ]

    operations = [
        migrations.RunPython(assign_roles_to_existing_users, reverse_migration),
    ]
