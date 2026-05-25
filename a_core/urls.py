"""
URL configuration for a_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include

from .views import home_view, health_check, liveness_probe, readiness_probe, robots_txt, sitemap_xml, security_txt
from .admin_honeypot import admin_honeypot_view
from services.metrics import metrics_view

admin.site.site_header = 'Trust Management Admin'
admin.site.site_title = 'Trust Management'
admin.site.index_title = 'Administration'

ADMIN_PATH = 'mgmt-console/'

urlpatterns = [
    path(ADMIN_PATH, admin.site.urls),
    path('admin/', admin_honeypot_view, name='admin_honeypot'),
    path('admin/<path:path>', admin_honeypot_view),
    path('health/', health_check, name='health_check'),
    path('health/live/', liveness_probe, name='liveness_probe'),
    path('health/ready/', readiness_probe, name='readiness_probe'),
    path('metrics/', metrics_view, name='metrics'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
    path('.well-known/security.txt', security_txt, name='security_txt'),
    path("", home_view, name='home'),
    path('auth/', include("a_customeauth.urls"),name='auth'),
    path('donation/', include("donations.urls"),name='donations'),
    # Phase 1
    path('roles/', include("roles.urls")),
    path('approvals/', include("approval_engine.urls")),
    # Phase 2
    path('expenses/', include("expenses.urls")),
    path('payments/', include("payments.urls")),
    path('notices/', include("notices.urls")),
    # Phase 3
    path('dashboard/', include("dashboard.urls")),
    path('reports/', include("reports.urls")),
    path('transparency/', include("transparency.urls")),
    # Phase 4
    path('chat/', include("chat.urls")),
    path('products/', include("products.urls")),
    path('ngo/', include("ngo_requests.urls")),
    # Config
    path('config/', include("config_app.urls")),
]

urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)

handler403 = 'a_core.error_handlers.custom_403'
handler404 = 'a_core.error_handlers.custom_404'
handler500 = 'a_core.error_handlers.custom_500'
