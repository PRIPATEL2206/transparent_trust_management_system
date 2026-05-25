from django import template
from roles.services import RoleService

register = template.Library()


@register.simple_tag
def user_role(user):
    return RoleService.get_user_role(user)


@register.simple_tag
def has_permission(user, permission):
    return RoleService.has_permission(user, permission)


@register.simple_tag
def has_role(user, *roles):
    return RoleService.has_role(user, *roles)
