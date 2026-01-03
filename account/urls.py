from django.urls import path
from .views import LoginView,RegisterView,logoutView


urlpatterns = [
    path("register/",RegisterView.as_view(),name="register"),
    path("login/",LoginView.as_view(),name="login"),
    path("logout/",logoutView,name="logout")
]