from django.contrib import admin
from .models import Notice, Notification


@admin.action(description='Approve selected notices')
def approve_notices(modeladmin, request, queryset):
    queryset.update(is_approved=True, is_active=True)


@admin.action(description='Deactivate selected notices')
def deactivate_notices(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'priority', 'is_approved', 'is_active', 'expires_at', 'created_at')
    list_filter = ('priority', 'is_approved', 'is_active')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = [approve_notices, deactivate_notices]


@admin.action(description='Mark selected as read')
def mark_notifications_read(modeladmin, request, queryset):
    queryset.update(is_read=True)


@admin.action(description='Delete read notifications')
def delete_read_notifications(modeladmin, request, queryset):
    queryset.filter(is_read=True).delete()


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = [mark_notifications_read, delete_read_notifications]
