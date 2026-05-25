from django.contrib.auth.models import User
from django.db.models import QuerySet

from services.base import BaseService, service_error_handler
from services.exceptions import PermissionDeniedError, NotFoundError, ValidationError
from .models import UserRole, RolePermission


ROLE_HIERARCHY = {
    'super_admin': 5,
    'admin': 4,
    'member': 3,
    'user': 2,
    'ngo': 1,
}

DEFAULT_PERMISSIONS = {
    'super_admin': [
        'manage_roles', 'manage_users', 'manage_config',
        'approve_content', 'manage_donations', 'manage_expenses',
        'view_reports', 'manage_notices', 'manage_chat',
        'manage_products', 'manage_ngo_requests', 'view_dashboard',
    ],
    'admin': [
        'approve_content', 'manage_donations', 'manage_expenses',
        'view_reports', 'manage_notices', 'manage_chat',
        'manage_products', 'manage_ngo_requests', 'view_dashboard',
    ],
    'member': [
        'create_donations', 'create_expenses', 'create_notices',
        'join_chat', 'view_transparency',
    ],
    'user': [
        'view_donations', 'make_payments', 'view_transparency',
    ],
    'ngo': [
        'create_fund_requests', 'view_transparency',
    ],
}


class RoleService(BaseService):

    @staticmethod
    @service_error_handler
    def get_user_role(user: User) -> str:
        try:
            return user.role_profile.role
        except UserRole.DoesNotExist:
            return 'user'

    @staticmethod
    @service_error_handler
    def get_or_create_role(user: User) -> UserRole:
        role, _ = UserRole.objects.get_or_create(user=user, defaults={'role': 'user'})
        return role

    @staticmethod
    @service_error_handler
    def has_permission(user: User, permission: str) -> bool:
        role = RoleService.get_user_role(user)
        if RolePermission.objects.filter(role=role, permission=permission).exists():
            return True
        return permission in DEFAULT_PERMISSIONS.get(role, [])

    @staticmethod
    @service_error_handler
    def has_role(user: User, *roles: str) -> bool:
        user_role = RoleService.get_user_role(user)
        return user_role in roles

    @staticmethod
    @service_error_handler
    def assign_role(user: User, role: str, approved_by: User = None) -> UserRole:
        valid_roles = [r[0] for r in UserRole.ROLE_CHOICES]
        if role not in valid_roles:
            raise ValidationError(f"Invalid role: {role}")

        user_role = RoleService.get_or_create_role(user)
        user_role.role = role
        user_role.approved = approved_by is not None
        user_role.approved_by = approved_by
        user_role.save()

        RoleService.log_action(
            'role_assigned',
            user=approved_by,
            target_user=user.username,
            new_role=role
        )
        return user_role

    @staticmethod
    @service_error_handler
    def get_users_by_role(role: str) -> QuerySet:
        return User.objects.filter(role_profile__role=role)

    @staticmethod
    @service_error_handler
    def can_manage_role(manager: User, target_role: str) -> bool:
        manager_role = RoleService.get_user_role(manager)
        manager_level = ROLE_HIERARCHY.get(manager_role, 0)
        target_level = ROLE_HIERARCHY.get(target_role, 0)
        return manager_level > target_level

    @staticmethod
    def get_role_hierarchy() -> dict:
        return ROLE_HIERARCHY
