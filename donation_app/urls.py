# urls.py
from django.urls import path
from .views import DonationCreateView, DonationListView

app_name = "donation_app"

urlpatterns = [
    path("donate/<slug:slug>/", DonationCreateView.as_view(), name="campaign_donate"),
    path("donations/", DonationListView.as_view(), name="donation_list"),
]
