from django.urls import path
from .views import LoginView,RegisterView,logoutView, ResendVerificationView, VerifyEmailView, ProfileUpdateView
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
    path('logout/', logoutView,name='logout'),
    
    # reset password
    path('password-reset/', PasswordResetView.as_view(template_name='account/password_reset.html', html_email_template_name='account/password_reset_email.html'),name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html'),name='password_reset_confirm'),
    path('password-reset-complete/',PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'),name='password_reset_complete'),

    # verify email
    path("verify_email_send/",LoginView.as_view(),name="verify_email_send"),
    path('email-sent/', TemplateView.as_view(template_name="account/email_sent.html"), name='email_sent'),
    path('verify-email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('email-verified/', TemplateView.as_view(template_name="account/email_success.html"), name='email_verified'),
    path('verification-failed/', TemplateView.as_view(template_name="account/failed_email_verification.html"), name='email_verification_failed'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    
    # profile
    # path('edit_profile', profile_view, name='profile'),
    path('edit_profile', ProfileUpdateView.as_view(), name='profile'),
]