from django.urls import path
from . import views

urlpatterns = [
    path('', views.approval_list_view, name='approvals_list'),
    path('<int:approval_id>/action/', views.approval_action_view, name='approvals_action'),
]
