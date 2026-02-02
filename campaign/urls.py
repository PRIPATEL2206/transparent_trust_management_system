from . import views,public_views
from django.urls import path

app_name = "campaign"

urlpatterns = [
    path('', views.CampaignListView.as_view(), name='list'),
    path('create', views.CreateUpdateCampaignView.as_view(), name='create'),
    path('<int:pk>/', views.CreateUpdateCampaignView.as_view(), name='update'),
    path('gallery_delete/<int:pk>/', views.CampaignGalaryImageDeleteView.as_view(), name='gallery_delete'),
    
    # public url
    path("public/", public_views.CampaignListView.as_view(), name="public_list"),
    path("<slug:slug>/", public_views.CampaignDetailView.as_view(), name="detail"),
   

]
