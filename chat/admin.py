from django.contrib import admin
from .models import ChatGroup, Message


@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    filter_horizontal = ('members',)
    ordering = ('-created_at',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'group', 'content', 'created_at')
    list_filter = ('group', 'created_at')
    search_fields = ('content', 'sender__username')
    ordering = ('-created_at',)
