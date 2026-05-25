from django.urls import path
from . import views

urlpatterns = [
    path('', views.transparency_view, name='transparency'),
]
