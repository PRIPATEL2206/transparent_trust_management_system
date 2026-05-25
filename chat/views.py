from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from roles.decorators import admin_required
from .models import ChatGroup, Message
from .forms import ChatGroupForm, AddMemberForm
from .services import ChatService


@login_required
def chat_group_list_view(request: HttpRequest):
    groups = ChatService.get_user_groups(request.user)
    context = {'groups': groups}
    return render(request, 'chat/group_list.html', context)


@login_required
def chat_room_view(request: HttpRequest, group_id: int):
    group = get_object_or_404(ChatGroup, id=group_id, members=request.user)

    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        if content:
            ChatService.send_message(group, request.user, content)
        return redirect('chat_room', group_id=group_id)

    recent_messages = ChatService.get_group_messages(group, limit=50)
    context = {
        'group': group,
        'messages_list': reversed(list(recent_messages)),
    }
    return render(request, 'chat/chat_room.html', context)


@admin_required
def chat_group_create_view(request: HttpRequest):
    form = ChatGroupForm()
    if request.method == 'POST':
        form = ChatGroupForm(request.POST)
        if form.is_valid():
            ChatService.create_group(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                created_by=request.user
            )
            messages.success(request, "Chat group created.")
            return redirect('chat_groups')
    return render(request, 'chat/group_form.html', {'form': form})


@admin_required
def chat_manage_members_view(request: HttpRequest, group_id: int):
    group = get_object_or_404(ChatGroup, id=group_id)
    add_form = AddMemberForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            add_form = AddMemberForm(request.POST)
            if add_form.is_valid():
                try:
                    user = User.objects.get(username=add_form.cleaned_data['username'])
                    ChatService.add_member(group, user, request.user)
                    messages.success(request, f"{user.username} added to group.")
                except User.DoesNotExist:
                    messages.error(request, "User not found.")
        elif action == 'remove':
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                ChatService.remove_member(group, user, request.user)
                messages.success(request, f"{user.username} removed from group.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")

        return redirect('chat_manage_members', group_id=group.id)

    context = {
        'group': group,
        'members': group.members.all(),
        'add_form': add_form,
    }
    return render(request, 'chat/manage_members.html', context)
