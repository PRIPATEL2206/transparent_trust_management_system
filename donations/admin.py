from django.contrib import admin
from services.admin_base import AuditModelAdmin
from .models import DonationType, Donation


@admin.register(DonationType)
class DonationTypeAdmin(AuditModelAdmin):
    list_display = ('name', 'created_by', 'starting_date', 'ending_date', 'is_forever')
    list_filter = ('is_forever',)
    search_fields = ('name', 'desc')


@admin.action(description='Approve selected donations')
def approve_donations(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.action(description='Reject (delete) selected donations')
def reject_donations(modeladmin, request, queryset):
    queryset.filter(is_approved=False).delete()


@admin.register(Donation)
class DonationAdmin(AuditModelAdmin):
    list_display = ('display_name', 'add_by', 'donation_for', 'amount', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'donation_for', 'created_at')
    search_fields = ('display_name', 'handover_by', 'desc', 'add_by__username')
    readonly_fields = ('add_by', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = [approve_donations, reject_donations]
