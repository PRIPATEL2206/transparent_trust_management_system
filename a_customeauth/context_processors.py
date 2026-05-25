def email_verification_context(request):
    if not request.user.is_authenticated:
        return {}

    from .email_verification import EmailVerificationService
    is_verified = EmailVerificationService.is_verified(request.user)
    return {
        'email_verified': is_verified,
        'show_verification_banner': not is_verified and hasattr(request.user, 'email') and request.user.email,
    }
