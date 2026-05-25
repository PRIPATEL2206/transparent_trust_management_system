from django.contrib.auth.models import User
from django.db.models import QuerySet

from services.base import BaseService, service_error_handler
from services.exceptions import PermissionDeniedError, ValidationError, NotFoundError
from .models import ChatGroup, Message


class ChatService(BaseService):

    @staticmethod
    @service_error_handler
    def create_group(name: str, description: str, created_by: User) -> ChatGroup:
        group = ChatGroup.objects.create(
            name=name,
            description=description,
            created_by=created_by
        )
        group.members.add(created_by)
        ChatService.log_action('group_created', user=created_by, group_id=group.id)
        return group

    @staticmethod
    @service_error_handler
    def add_member(group: ChatGroup, user: User, added_by: User) -> None:
        if group.created_by != added_by:
            from roles.services import RoleService
            if not RoleService.has_role(added_by, 'admin', 'super_admin'):
                raise PermissionDeniedError("Only group creator or admins can add members")
        group.members.add(user)
        ChatService.log_action('member_added', user=added_by, group_id=group.id, member=user.username)

    @staticmethod
    @service_error_handler
    def remove_member(group: ChatGroup, user: User, removed_by: User) -> None:
        if group.created_by != removed_by and user != removed_by:
            from roles.services import RoleService
            if not RoleService.has_role(removed_by, 'admin', 'super_admin'):
                raise PermissionDeniedError("Only group creator or admins can remove members")
        group.members.remove(user)
        ChatService.log_action('member_removed', user=removed_by, group_id=group.id, member=user.username)

    @staticmethod
    @service_error_handler
    def send_message(group: ChatGroup, sender: User, content: str) -> Message:
        if not group.members.filter(id=sender.id).exists():
            raise PermissionDeniedError("You are not a member of this group")
        if not content.strip():
            raise ValidationError("Message cannot be empty")
        if len(content) > 2000:
            raise ValidationError("Message is too long (max 2000 characters)")

        message = Message.objects.create(
            group=group,
            sender=sender,
            content=content.strip()
        )
        return message

    @staticmethod
    def get_user_groups(user: User) -> QuerySet:
        return ChatGroup.objects.filter(members=user, is_active=True).order_by('-created_at')

    @staticmethod
    def get_group_messages(group: ChatGroup, limit: int = 50) -> QuerySet:
        return Message.objects.filter(group=group).select_related('sender').order_by('-created_at')[:limit]
