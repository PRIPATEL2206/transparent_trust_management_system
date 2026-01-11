from django.urls import path
from .views import LoginView,RegisterView,logoutView, ResendVerificationView, VerifyEmailView, profile_view
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', LoginView.as_view(),name='login'),
    path("register/",RegisterView.as_view(),name="register"),
    path('password-reset/', PasswordResetView.as_view(template_name='account/password_reset.html', html_email_template_name='account/password_reset_email.html'),name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html'),name='password_reset_confirm'),
    path('password-reset-complete/',PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'),name='password_reset_complete'),
    path("verify_email_send/",LoginView.as_view(),name="verify_email_send"),
    path('logout/', logoutView,name='logout'),
    path('email-sent/', TemplateView.as_view(template_name="account/email_sent.html"), name='email_sent'),
    path('verify-email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('email-verified/', TemplateView.as_view(template_name="account/email_success.html"), name='email_verified'),
    path('verification-failed/', TemplateView.as_view(template_name="account/failed_email_verification.html"), name='email_verification_failed'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    path('edit_profile', profile_view, name='profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)