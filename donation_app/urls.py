# urls.py
from django.urls import path
from .views import DonationCreateView

app_name = "donation_app"

urlpatterns = [
    path("donate/<slug:slug>/", DonationCreateView.as_view(), name="campaign_donate"),
]