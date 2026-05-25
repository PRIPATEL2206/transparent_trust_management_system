from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_generate_view, name='reports_generate'),
    path('<int:report_id>/download/', views.report_download_view, name='reports_download'),
]
