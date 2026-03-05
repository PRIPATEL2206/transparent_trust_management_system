from django.urls import path
from . import views

app_name = "payment_app"


urlpatterns = [
    path("success/",views.PaymentSuccessView.as_view(),name='payment_success'),
    path("cancelled/",views.PaymentCancelledView.as_view(),name='payment_cancelled')
]