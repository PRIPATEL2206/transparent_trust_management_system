from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_create_view, name='payments_create'),
    path('history/', views.payment_history_view, name='payments_history'),
    path('receipt/<int:transaction_id>/', views.receipt_download_view, name='payments_receipt'),
    path('admin/', views.payment_admin_view, name='payments_admin'),
    path('admin/export/', views.payment_export_view, name='payments_export'),
]
