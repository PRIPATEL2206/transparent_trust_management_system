from . import views
from django.urls import path

app_name = "campaign"

urlpatterns = [
    path('', views.CampaignListView.as_view(), name='list'),
    path('create', views.CreateCampaignView.as_view(), name='create'),
    # path("<slug:slug>/", views.campaign_detail, name="detail"),
    # path("<slug:slug>/edit/", views.campaign_edit, name="edit")
]
