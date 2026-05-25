import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailVerification

logger = logging.getLogger('services')


class EmailVerificationService:

    @staticmethod
    def create_verification(user):
        verification, created = EmailVerification.objects.get_or_create(
            user=user,
            defaults={'last_sent_at': timezone.now()}
        )
        if not created and not verification.is_verified:
            verification.regenerate_token()
        return verification

    @staticmethod
    def send_verification_email(user, request=None):
        verification = EmailVerificationService.create_verification(user)

        if verification.is_verified:
            return False

        if verification.resend_count >= 5:
            return False

        scheme = 'https' if request and request.is_secure() else 'http'
        host = request.get_host() if request else settings.ALLOWED_HOSTS[0]
        verify_url = f"{scheme}://{host}/auth/verify-email/{verification.token}/"

        context = {
            'user': user,
            'verify_url': verify_url,
            'expiry_hours': 24,
        }

        subject = 'Verify your email - Trust Management System'
        message = render_to_string('customauth/email_verification.txt', context)
        html_message = render_to_string('customauth/email_verification_html.html', context)

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            verification.last_sent_at = timezone.now()
            verification.save(update_fields=['last_sent_at'])
            logger.info(f"Verification email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")
            return False

    @staticmethod
    def verify_token(token):
        try:
            verification = EmailVerification.objects.select_related('user').get(token=token)
        except EmailVerification.DoesNotExist:
            return None, 'invalid'

        if verification.is_verified:
            return verification.user, 'already_verified'

        if verification.is_expired:
            return verification.user, 'expired'

        verification.verify()
        return verification.user, 'success'

    @staticmethod
    def is_verified(user):
        if not user.is_authenticated:
            return False
        try:
            return user.email_verification.is_verified
        except EmailVerification.DoesNotExist:
            return False

    @staticmethod
    def can_resend(user):
        try:
            verification = user.email_verification
            if verification.is_verified:
                return False
            if verification.resend_count >= 5:
                return False
            if verification.last_sent_at:
                cooldown = timezone.now() - verification.last_sent_at
                if cooldown.total_seconds() < 60:
                    return False
            return True
        except EmailVerification.DoesNotExist:
            return True
