from django.urls import path
from .views import (
    add_donation_types, add_donation, donation_type_page_view,
    donation_page_view, donation_admin_view, donation_action_view,
    donation_export_view
)


urlpatterns = [
    path('add-donation-types/',add_donation_types,name='add_donation_types'),
    path('add-donation/',add_donation,name='add_donation'),
    path('donation/',donation_type_page_view,name='donations_types'),
    path('donation/<int:id>',donation_page_view,name='donations'),
    path('donations/admin/', donation_admin_view, name='donations_admin'),
    path('donations/admin/export/', donation_export_view, name='donations_export'),
    path('donations/<int:donation_id>/action/', donation_action_view, name='donations_action'),
]
