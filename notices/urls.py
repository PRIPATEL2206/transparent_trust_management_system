from django.urls import path
from . import views

urlpatterns = [
    path('', views.notice_list_view, name='notices_list'),
    path('create/', views.notice_create_view, name='notices_create'),
    path('admin/', views.notice_admin_view, name='notices_admin'),
    path('<int:notice_id>/approve/', views.notice_approve_view, name='notices_approve'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read_view, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read_view, name='notifications_mark_all_read'),
]
