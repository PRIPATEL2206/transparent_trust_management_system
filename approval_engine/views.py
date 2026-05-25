from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from roles.decorators import admin_required
from .models import ApprovalRequest
from .services import ApprovalService


@admin_required
def approval_list_view(request: HttpRequest):
    status_filter = request.GET.get('status', 'pending')
    content_type_filter = request.GET.get('type', '')

    approvals = ApprovalRequest.objects.select_related(
        'requested_by', 'reviewed_by', 'content_type'
    ).order_by('-created_at')

    if status_filter:
        approvals = approvals.filter(status=status_filter)
    if content_type_filter:
        approvals = approvals.filter(content_type__model=content_type_filter)

    paginator = Paginator(approvals, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page': page,
        'status_filter': status_filter,
        'content_type_filter': content_type_filter,
    }
    return render(request, 'approval_engine/approval_list.html', context)


@admin_required
@require_POST
def approval_action_view(request: HttpRequest, approval_id: int):
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')

    if action == 'approve':
        ApprovalService.approve(approval_id, request.user, notes)
        messages.success(request, "Request approved successfully.")
    elif action == 'reject':
        ApprovalService.reject(approval_id, request.user, notes)
        messages.success(request, "Request rejected.")

    return redirect('approvals_list')
