from . import views
from django.urls import path

app_name = "campaign"

urlpatterns = [
    path('', views.CampaignListView.as_view(), name='list'),
    path('create', views.CreateUpdateCampaignView.as_view(), name='create'),
    path('<int:pk>/', views.CreateUpdateCampaignView.as_view(), name='update'),
    path('gallery_delete/<int:pk>/', views.CampaignGalaryImageDeleteView.as_view(), name='gallery_delete'),
    # path("<slug:slug>/", views.campaign_detail, name="detail"),
]
