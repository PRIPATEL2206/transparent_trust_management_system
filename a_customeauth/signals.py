from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth.models import User

from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    user: User = instance
    if created:
        Profile.objects.create(user=user)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    from dashboard.services import ActivityLogService
    ActivityLogService.log(
        user, "Logged in",
        category='auth', request=request
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    from dashboard.services import ActivityLogService
    if user:
        ActivityLogService.log(
            user, "Logged out",
            category='auth', request=request
        )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    from dashboard.services import ActivityLogService
    ActivityLogService.log(
        None, f"Failed login attempt for '{credentials.get('username', 'unknown')}'",
        category='auth', request=request
    )