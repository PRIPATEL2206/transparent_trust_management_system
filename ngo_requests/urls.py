from django.urls import path
from . import views

urlpatterns = [
    path('', views.fund_request_list_view, name='ngo_requests_list'),
    path('create/', views.fund_request_create_view, name='ngo_requests_create'),
    path('admin/', views.fund_request_admin_view, name='ngo_requests_admin'),
    path('<int:request_id>/action/', views.fund_request_action_view, name='ngo_requests_action'),
]
