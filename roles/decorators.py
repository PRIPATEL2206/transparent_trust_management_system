from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from .services import RoleService


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('auth_login')
            if not RoleService.has_role(request.user, *roles):
                messages.error(request, "You don't have permission to access this page.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('auth_login')
            if not RoleService.has_permission(request.user, permission):
                messages.error(request, "You don't have permission to perform this action.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth_login')
        if not RoleService.has_role(request.user, 'admin', 'super_admin'):
            messages.error(request, "Admin access required.")
            return redirect('home')
        from a_customeauth.totp_service import TOTPService
        if TOTPService.requires_2fa(request.user) and not TOTPService.is_2fa_enabled(request.user):
            messages.warning(request, "Two-factor authentication is required for admin accounts.")
            return redirect('auth_2fa_setup')
        if not request.session.get('2fa_verified') and TOTPService.is_2fa_enabled(request.user):
            messages.warning(request, "Please verify your 2FA to access admin features.")
            return redirect('auth_2fa_verify')
        response = view_func(request, *args, **kwargs)
        response['X-Robots-Tag'] = 'noindex, nofollow'
        return response
    return wrapper
