from django.contrib import admin
from .models import FundRequest


@admin.register(FundRequest)
class FundRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'ngo_user', 'amount_requested', 'amount_approved', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'ngo_user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
