from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.conf.urls.static import static
from django.conf import settings
from services.rate_limit import rate_limit
from .views import login_view, profile_view, register_view, logout_view, settings_view, export_my_data_view, verify_email_view, resend_verification_view
from .views_2fa import setup_2fa_view, confirm_2fa_view, disable_2fa_view, verify_2fa_view, regenerate_backup_codes_view


urlpatterns = [
    path('login/',login_view,name='auth_login'),
    path('register/',register_view,name='auth_register'),
    path('profile/',profile_view,name='auth_profile'),
    path('settings/',settings_view,name='auth_settings'),
    path('export-data/', export_my_data_view, name='auth_export_data'),
    path('verify-email/<uuid:token>/', verify_email_view, name='auth_verify_email'),
    path('verify-email/resend/', resend_verification_view, name='auth_resend_verification'),
    # 2FA
    path('2fa/setup/', setup_2fa_view, name='auth_2fa_setup'),
    path('2fa/confirm/', confirm_2fa_view, name='auth_2fa_confirm'),
    path('2fa/verify/', login_not_required(verify_2fa_view), name='auth_2fa_verify'),
    path('2fa/disable/', disable_2fa_view, name='auth_2fa_disable'),
    path('2fa/backup-codes/', regenerate_backup_codes_view, name='auth_2fa_backup_codes'),
    path('logout/',logout_view,name='auth_logout'),
    path('password-reset/', rate_limit(max_attempts=3, window=600, key_prefix='pwd_reset')(login_not_required(auth_views.PasswordResetView.as_view(
        template_name='customauth/password_reset.html',
        email_template_name='customauth/password_reset_email.html',
        subject_template_name='customauth/password_reset_subject.txt',
        success_url='/auth/password-reset/done/'
    ))), name='password_reset'),
    path('password-reset/done/', login_not_required(auth_views.PasswordResetDoneView.as_view(
        template_name='customauth/password_reset_done.html'
    )), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', login_not_required(auth_views.PasswordResetConfirmView.as_view(
        template_name='customauth/password_reset_confirm.html',
        success_url='/auth/password-reset-complete/'
    )), name='password_reset_confirm'),
    path('password-reset-complete/', login_not_required(auth_views.PasswordResetCompleteView.as_view(
        template_name='customauth/password_reset_complete.html'
    )), name='password_reset_complete'),
]
