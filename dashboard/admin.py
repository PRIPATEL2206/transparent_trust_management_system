from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'category', 'target_user', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('user__username', 'action', 'target_user__username')
    readonly_fields = ('user', 'action', 'category', 'target_user', 'details', 'ip_address', 'created_at')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
