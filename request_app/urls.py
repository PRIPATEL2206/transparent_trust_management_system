from django.urls import path
from . import views

app_name = "request_app"

urlpatterns = [
    path("update/<int:pk>/", views.RequestUpdateStatusView.as_view(), name="update"),
    path("add-massage/<int:pk>/", views.RequestMessageCreateView.as_view(), name="add_massage"),
    path("<int:pk>/", views.RequestDetailView.as_view(), name="detail"),
    path("", views.RequestListView.as_view(), name="list"),
]
