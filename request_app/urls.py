from django.urls import path
from . import views

app_name = "request_app"

urlpatterns = [
    path("<int:pk>/", views.RequestDetailView.as_view(), name="detail")
]
