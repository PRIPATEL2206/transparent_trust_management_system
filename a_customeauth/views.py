from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sessions.models import Session
from django.middleware.csrf import rotate_token
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST
import json

from .forms import ProfileUpdateForm, RegisterForm
from .email_verification import EmailVerificationService
from .totp_service import TOTPService
from services.rate_limit import rate_limit
from services.app_metrics import track_login_success, track_login_failure, track_registration
from services.audit import log_login_success, log_login_failure, log_logout as audit_logout


@login_not_required
@rate_limit(max_attempts=5, window=300, key_prefix='login')
def login_view(request: HttpRequest):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, 'customauth/login.html')

        from django.core.cache import cache
        account_key = f'login_lockout:{username.lower()}'
        account_attempts = cache.get(account_key, 0)
        if account_attempts >= 5:
            messages.error(request, "This account is temporarily locked due to too many failed attempts. Try again later.")
            return render(request, 'customauth/login.html')

        user = authenticate(request=request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account has been deactivated. Contact an admin.")
            elif TOTPService.is_2fa_enabled(user):
                request.session['2fa_pending_user_id'] = user.pk
                next_url = request.GET.get('next', '/')
                if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    next_url = '/'
                request.session['2fa_next_url'] = next_url
                cache.delete(account_key)
                _record_login(request, user, success=True)
                return redirect('auth_2fa_verify')
            else:
                _enforce_max_sessions(user)
                login(request, user)
                rotate_token(request)
                cache.delete(account_key)
                _record_login(request, user, success=True)
                track_login_success()
                log_login_success(user)
                from .signals_security import user_logged_in_custom, new_ip_login
                user_logged_in_custom.send(sender=user.__class__, user=user, request=request)
                _check_new_ip(request, user)
                messages.success(request, "Login successful.")
                next_url = request.GET.get('next', '/')
                if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    next_url = '/'
                return redirect(next_url)
        else:
            new_count = account_attempts + 1
            cache.set(account_key, new_count, 300)
            _record_login_by_username(request, username, success=False)
            track_login_failure()
            log_login_failure(username)
            if new_count >= 5:
                _send_lockout_notification(username)
                from .signals_security import account_locked
                account_locked.send(sender=None, username=username, request=request)
            messages.error(request, "Invalid username or password.")

    return render(request, 'customauth/login.html')


@login_not_required
@rate_limit(max_attempts=3, window=600, key_prefix='register')
def register_view(request: HttpRequest):
    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            EmailVerificationService.send_verification_email(user, request)
            track_registration()
            login(request, user)
            messages.success(request, "Registration successful. Please check your email to verify your account.")
            return redirect('home')

    return render(request, 'customauth/register.html', {'form': form})


@require_POST
def logout_view(request: HttpRequest):
    audit_logout(request.user)
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('auth_login')


def profile_view(request: HttpRequest):
    user = request.user

    data = {
        'avatar': user.profile.avatar,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }
    form = ProfileUpdateForm(initial=data, current_user=user)

    if request.POST:
        form = ProfileUpdateForm(initial=data, data=request.POST, files=request.FILES, current_user=user)
        if form.is_valid():
            data = form.cleaned_data
            user.username = data.get('username')
            user.first_name = data.get('first_name')
            user.last_name = data.get('last_name')
            user.email = data.get('email')
            user.profile.avatar = data.get('avatar')
            user.save()
            user.profile.save()
            messages.success(request, "Profile updated.")

    from roles.services import RoleService
    from dashboard.services import ActivityLogService
    user_role = RoleService.get_user_role(user)
    recent_activity = ActivityLogService.get_user_activity(user, limit=5)

    context = {
        'form': form,
        'user_role': user_role,
        'recent_activity': recent_activity,
    }
    return render(request, 'customauth/profile_page.html', context)


def settings_view(request: HttpRequest):
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                current_session_key = request.session.session_key
                update_session_auth_hash(request, user)
                _flush_other_sessions(user, current_session_key)
                if hasattr(user, 'profile'):
                    user.profile.password_changed_at = timezone.now()
                    user.profile.save(update_fields=['password_changed_at'])
                from services.audit import log_password_change
                log_password_change(user)
                messages.success(request, "Password changed successfully.")
                return redirect('auth_settings')
            else:
                messages.error(request, "Please correct the errors below.")

        elif 'deactivate_account' in request.POST:
            confirmation = request.POST.get('confirm_deactivate', '')
            if confirmation == request.user.username:
                request.user.is_active = False
                request.user.save()
                logout(request)
                messages.success(request, "Your account has been deactivated.")
                return redirect('auth_login')
            else:
                messages.error(request, "Username confirmation did not match.")

    context = {
        'password_form': password_form,
        'totp_enabled': TOTPService.is_2fa_enabled(request.user),
        'totp_required': TOTPService.requires_2fa(request.user),
        'backup_codes_remaining': getattr(getattr(request.user, 'totp_device', None), 'backup_codes_remaining', 0),
    }
    return render(request, 'customauth/settings.html', context)


@rate_limit(max_attempts=3, window=600, key_prefix='data_export')
def export_my_data_view(request: HttpRequest):
    """Export all user data as JSON (GDPR-style data export)."""
    user = request.user

    from donations.models import Donation
    from expenses.models import Expense
    from payments.models import Transaction
    from products.models import Order

    data = {
        'account': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        },
        'donations': list(
            Donation.objects.filter(add_by=user).values(
                'display_name', 'amount', 'desc', 'is_approved', 'created_at'
            )
        ),
        'expenses': list(
            Expense.objects.filter(raised_by=user).values(
                'title', 'amount', 'status', 'created_at'
            )
        ),
        'transactions': list(
            Transaction.objects.filter(user=user).values(
                'transaction_type', 'amount', 'status', 'created_at'
            )
        ),
        'orders': list(
            Order.objects.filter(user=user).values(
                'product__name', 'quantity', 'total_amount', 'status', 'created_at'
            )
        ),
    }

    response = JsonResponse(data, json_dumps_params={'indent': 2, 'default': str})
    response['Content-Disposition'] = f'attachment; filename="{user.username}_data_export.json"'
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response['X-Content-Type-Options'] = 'nosniff'
    response['X-Download-Options'] = 'noopen'
    return response


def _flush_other_sessions(user, current_session_key):
    """Delete all sessions for a user except the current one."""
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions.iterator():
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.pk) and session.session_key != current_session_key:
            session.delete()


def _flush_all_sessions(user):
    """Delete all sessions for a user (used on account deactivation)."""
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions.iterator():
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.pk):
            session.delete()


def _enforce_max_sessions(user, max_sessions=3):
    """Evict oldest sessions if user exceeds max concurrent sessions."""
    from django.conf import settings
    max_sessions = getattr(settings, 'MAX_SESSIONS_PER_USER', max_sessions)
    user_sessions = []
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions.iterator():
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.pk):
            user_sessions.append(session)
    if len(user_sessions) >= max_sessions:
        user_sessions.sort(key=lambda s: s.expire_date)
        for session in user_sessions[:len(user_sessions) - max_sessions + 1]:
            session.delete()


def _send_lockout_notification(username):
    """Send email notification when an account gets locked out."""
    try:
        user = User.objects.get(username__iexact=username)
        if user.email:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                subject='Account Locked - Suspicious Login Activity',
                message=(
                    f'Hi {user.username},\n\n'
                    f'Your account has been temporarily locked due to multiple failed login attempts. '
                    f'If this was not you, please reset your password immediately.\n\n'
                    f'The lock will expire in 5 minutes.\n\n'
                    f'- Trust Management System'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
    except User.DoesNotExist:
        pass


def _record_login(request, user, success=True):
    """Record a login event in login history."""
    from .models import LoginHistory
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '0.0.0.0')
    ua = request.META.get('HTTP_USER_AGENT', '')[:300]
    LoginHistory.objects.create(user=user, ip_address=ip, user_agent=ua, success=success)


def _record_login_by_username(request, username, success=False):
    """Record a failed login attempt by username."""
    try:
        user = User.objects.get(username__iexact=username)
        _record_login(request, user, success=success)
    except User.DoesNotExist:
        pass


def _check_new_ip(request, user):
    """Fire signal if this IP has never been seen for this user before."""
    from .models import LoginHistory
    from .signals_security import new_ip_login
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '0.0.0.0')
    if not LoginHistory.objects.filter(user=user, ip_address=ip, success=True).exclude(pk=LoginHistory.objects.filter(user=user).order_by('-created_at').values_list('pk', flat=True)[:1]).exists():
        seen_before = LoginHistory.objects.filter(user=user, ip_address=ip, success=True).count()
        if seen_before <= 1:
            new_ip_login.send(sender=None, user=user, ip_address=ip, request=request)


@login_not_required
def verify_email_view(request: HttpRequest, token):
    user, status = EmailVerificationService.verify_token(token)

    if status == 'success':
        messages.success(request, "Email verified successfully! Your account is now fully activated.")
    elif status == 'already_verified':
        messages.info(request, "Your email has already been verified.")
    elif status == 'expired':
        messages.warning(request, "This verification link has expired. Please request a new one.")
        if user and request.user.is_authenticated and request.user == user:
            return redirect('auth_resend_verification')
    else:
        messages.error(request, "Invalid verification link.")

    return redirect('home')


@rate_limit(max_attempts=3, window=300, key_prefix='resend_verify')
def resend_verification_view(request: HttpRequest):
    user = request.user

    if EmailVerificationService.is_verified(user):
        messages.info(request, "Your email is already verified.")
        return redirect('auth_profile')

    if not EmailVerificationService.can_resend(user):
        messages.warning(request, "Please wait before requesting another verification email.")
        return render(request, 'customauth/verification_pending.html')

    if request.method == 'POST':
        sent = EmailVerificationService.send_verification_email(user, request)
        if sent:
            messages.success(request, "Verification email sent! Check your inbox.")
        else:
            messages.error(request, "Could not send verification email. Please try again later.")
        return redirect('auth_resend_verification')

    return render(request, 'customauth/verification_pending.html')
