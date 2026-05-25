from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .totp_service import TOTPService
from services.rate_limit import rate_limit
from services.audit import log_2fa_event


@login_required
def setup_2fa_view(request: HttpRequest):
    if TOTPService.is_2fa_enabled(request.user):
        messages.info(request, "Two-factor authentication is already enabled.")
        return redirect('auth_settings')

    device = TOTPService.setup_2fa(request.user)
    uri = TOTPService.get_provisioning_uri(request.user, device.secret)
    qr_data_url = TOTPService.generate_qr_data_url(uri)

    context = {
        'secret': device.secret,
        'qr_data_url': qr_data_url,
        'provisioning_uri': uri,
    }
    return render(request, 'customauth/2fa_setup.html', context)


@login_required
@rate_limit(max_attempts=5, window=300, key_prefix='2fa_confirm')
def confirm_2fa_view(request: HttpRequest):
    if request.method != 'POST':
        return redirect('auth_2fa_setup')

    code = request.POST.get('code', '').strip()
    if not code:
        messages.error(request, "Please enter the verification code.")
        return redirect('auth_2fa_setup')

    backup_codes, status = TOTPService.confirm_2fa(request.user, code)

    if status == 'success':
        log_2fa_event('enabled', request.user)
        messages.success(request, "Two-factor authentication enabled successfully!")
        request.session['2fa_verified'] = True
        return render(request, 'customauth/2fa_backup_codes.html', {
            'backup_codes': backup_codes,
        })
    elif status == 'invalid_code':
        messages.error(request, "Invalid code. Please try again.")
        return redirect('auth_2fa_setup')
    elif status == 'already_confirmed':
        messages.info(request, "2FA is already enabled.")
        return redirect('auth_settings')
    else:
        messages.error(request, "Please set up 2FA first.")
        return redirect('auth_2fa_setup')


@login_required
@require_POST
def disable_2fa_view(request: HttpRequest):
    password = request.POST.get('password', '')
    if not request.user.check_password(password):
        messages.error(request, "Incorrect password. 2FA was not disabled.")
        return redirect('auth_settings')

    TOTPService.disable_2fa(request.user)
    log_2fa_event('disabled', request.user)
    messages.success(request, "Two-factor authentication has been disabled.")
    return redirect('auth_settings')


def verify_2fa_view(request: HttpRequest):
    user_id = request.session.get('2fa_pending_user_id')
    if not user_id:
        return redirect('auth_login')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()

        from django.contrib.auth.models import User
        from django.contrib.auth import login

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            del request.session['2fa_pending_user_id']
            return redirect('auth_login')

        if TOTPService.verify_login(user, code):
            del request.session['2fa_pending_user_id']
            login(request, user)
            request.session['2fa_verified'] = True
            log_2fa_event('verified', user)
            messages.success(request, "Login successful.")
            next_url = request.session.pop('2fa_next_url', '/')
            return redirect(next_url)
        else:
            log_2fa_event('verify_failed', user, outcome='failure')
            messages.error(request, "Invalid verification code or backup code.")

    return render(request, 'customauth/2fa_verify.html')


@login_required
@require_POST
def regenerate_backup_codes_view(request: HttpRequest):
    password = request.POST.get('password', '')
    if not request.user.check_password(password):
        messages.error(request, "Incorrect password.")
        return redirect('auth_settings')

    if not TOTPService.is_2fa_enabled(request.user):
        messages.error(request, "2FA is not enabled.")
        return redirect('auth_settings')

    device = request.user.totp_device
    backup_codes = device.generate_backup_codes()
    messages.success(request, "New backup codes generated. Save them securely!")
    return render(request, 'customauth/2fa_backup_codes.html', {
        'backup_codes': backup_codes,
    })
