from django.urls import path
from . import views

urlpatterns = [
    path('', views.expense_list_view, name='expenses_list'),
    path('create/', views.expense_create_view, name='expenses_create'),
    path('<int:expense_id>/submit/', views.expense_submit_view, name='expenses_submit'),
    path('admin/', views.expense_admin_list_view, name='expenses_admin_list'),
    path('admin/export/', views.expense_export_view, name='expenses_export'),
    path('<int:expense_id>/action/', views.expense_action_view, name='expenses_action'),
]
