from django.contrib import admin
from .models import ApprovalRequest


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'object_id', 'requested_by', 'status', 'reviewed_by', 'created_at')
    list_filter = ('status', 'content_type', 'created_at')
    search_fields = ('requested_by__username', 'notes')
    readonly_fields = ('content_type', 'object_id', 'requested_by', 'created_at')
    date_hierarchy = 'created_at'
