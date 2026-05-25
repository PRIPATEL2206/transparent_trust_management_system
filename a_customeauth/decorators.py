from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def email_verified_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth_login')

        from .email_verification import EmailVerificationService
        if not EmailVerificationService.is_verified(request.user):
            messages.warning(request, "Please verify your email address to access this feature.")
            return redirect('auth_resend_verification')

        return view_func(request, *args, **kwargs)
    return wrapper
