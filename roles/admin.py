from django.contrib import admin
from services.admin_base import AuditModelAdmin
from .models import UserRole, RolePermission


@admin.register(UserRole)
class UserRoleAdmin(AuditModelAdmin):
    list_display = ('user', 'role', 'approved', 'approved_by', 'created_at')
    list_filter = ('role', 'approved')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(RolePermission)
class RolePermissionAdmin(AuditModelAdmin):
    list_display = ('role', 'permission', 'description')
    list_filter = ('role',)
    search_fields = ('permission', 'description')

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
