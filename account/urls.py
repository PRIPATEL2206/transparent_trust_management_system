from django.urls import path
from .views import LoginView,RegisterView,logoutView
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView,
    PasswordResetCompleteView
)


urlpatterns = [
    path('login/', LoginView.as_view(),name='login'),
    path("register/",RegisterView.as_view(),name="register"),
    path('password-reset/', PasswordResetView.as_view(template_name='account/password_reset.html', html_email_template_name='account/password_reset_email.html'),name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html'),name='password_reset_confirm'),
    path('password-reset-complete/',PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'),name='password_reset_complete'),
    path("verify_email_send/",LoginView.as_view(),name="verify_email_send"),
    path('logout/', logoutView,name='logout')
]