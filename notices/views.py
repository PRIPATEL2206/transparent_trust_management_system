from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page

from roles.decorators import admin_required, role_required
from services.pagination import safe_paginate
from .models import Notice, Notification
from .forms import NoticeForm
from .services import NoticeService, NotificationService


@login_not_required
@cache_page(60)
def notice_list_view(request: HttpRequest):
    notices = NoticeService.get_active_notices()
    page, _ = safe_paginate(notices, request)
    context = {'page': page}
    return render(request, 'notices/notice_list.html', context)


@role_required('member', 'admin', 'super_admin')
def notice_create_view(request: HttpRequest):
    form = NoticeForm()
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            NoticeService.create_notice(
                user=request.user,
                title=data['title'],
                content=data['content'],
                priority=data['priority'],
                expires_at=data.get('expires_at')
            )
            messages.success(request, "Notice created and submitted for approval.")
            return redirect('notices_list')
    return render(request, 'notices/notice_form.html', {'form': form})


@admin_required
def notice_admin_view(request: HttpRequest):
    pending = NoticeService.get_pending_notices()
    context = {'pending_notices': pending}
    return render(request, 'notices/notice_admin.html', context)


@admin_required
@require_POST
def notice_approve_view(request: HttpRequest, notice_id: int):
    notice = get_object_or_404(Notice, id=notice_id)
    action = request.POST.get('action')
    if action == 'approve':
        NoticeService.approve_notice(notice, request.user)
        NotificationService.send(
            notice.created_by, "Notice Approved",
            f"Your notice '{notice.title}' has been approved and is now live.",
            notification_type='success', link='/notices/'
        )
        messages.success(request, "Notice approved.")
    elif action == 'reject':
        NoticeService.deactivate_notice(notice, request.user)
        NotificationService.send(
            notice.created_by, "Notice Rejected",
            f"Your notice '{notice.title}' was rejected by an admin.",
            notification_type='warning'
        )
        messages.success(request, "Notice rejected.")
    return redirect('notices_admin')


def notifications_view(request: HttpRequest):
    notifications = Notification.objects.filter(recipient=request.user).select_related('recipient').order_by('-created_at')
    page, _ = safe_paginate(notifications, request, default_per_page=20)
    context = {'page': page}
    return render(request, 'notices/notifications.html', context)


@require_POST
def mark_notification_read_view(request: HttpRequest, notification_id: int):
    NotificationService.mark_read(notification_id, request.user)
    return redirect('notifications')


@require_POST
def mark_all_notifications_read_view(request: HttpRequest):
    NotificationService.mark_all_read(request.user)
    return redirect('notifications')
