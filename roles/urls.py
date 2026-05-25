from django.urls import path
from . import views

urlpatterns = [
    path('', views.role_list_view, name='roles_list'),
    path('assign/<int:user_id>/', views.assign_role_view, name='roles_assign'),
    path('pending/', views.pending_approvals_view, name='roles_pending'),
    path('approve/<int:role_id>/', views.approve_role_view, name='roles_approve'),
    path('request/', views.role_request_view, name='role_request'),
    path('request/<int:request_id>/action/', views.role_request_action_view, name='role_request_action'),
    path('members/', views.members_directory_view, name='members_directory'),
    path('members/<int:user_id>/toggle-active/', views.toggle_user_active_view, name='toggle_user_active'),
]
