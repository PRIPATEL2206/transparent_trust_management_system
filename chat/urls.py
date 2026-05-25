from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_group_list_view, name='chat_groups'),
    path('create/', views.chat_group_create_view, name='chat_create_group'),
    path('<int:group_id>/', views.chat_room_view, name='chat_room'),
    path('<int:group_id>/members/', views.chat_manage_members_view, name='chat_manage_members'),
]
