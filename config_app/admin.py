from django.contrib import admin
from .models import SiteConfig


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Trust Information', {
            'fields': ('trust_name', 'trust_description')
        }),
        ('Fees & Limits', {
            'fields': ('membership_fee', 'user_join_fee', 'min_donation_amount')
        }),
        ('SEO / Meta', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('Contact', {
            'fields': ('contact_email', 'contact_phone', 'address')
        }),
        ('Payment Gateway', {
            'fields': ('razorpay_key_id', 'razorpay_key_secret'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
