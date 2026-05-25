from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('activity/', views.activity_log_view, name='activity_log'),
    path('activity/export/', views.activity_log_export_view, name='activity_log_export'),
]
