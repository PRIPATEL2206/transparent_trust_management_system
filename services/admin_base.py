import logging

from django.contrib import admin
from django.contrib.admin.models import LogEntry

logger = logging.getLogger('services')


class AuditModelAdmin(admin.ModelAdmin):
    """Base admin class that logs all admin actions for audit purposes."""

    def save_model(self, request, obj, form, change):
        action = 'changed' if change else 'added'
        logger.info(
            'Admin %s %s %s (pk=%s) [%s]',
            request.user.username, action,
            obj.__class__.__name__, obj.pk,
            getattr(request, 'request_id', '-')
        )
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        logger.warning(
            'Admin %s deleted %s (pk=%s) [%s]',
            request.user.username,
            obj.__class__.__name__, obj.pk,
            getattr(request, 'request_id', '-')
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        count = queryset.count()
        logger.warning(
            'Admin %s bulk deleted %d %s objects [%s]',
            request.user.username, count,
            queryset.model.__name__,
            getattr(request, 'request_id', '-')
        )
        super().delete_queryset(request, queryset)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """Read-only admin log viewer for audit trail."""

    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'change_message')
    list_filter = ('action_flag', 'content_type', 'user')
    search_fields = ('object_repr', 'change_message')
    date_hierarchy = 'action_time'
    readonly_fields = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
