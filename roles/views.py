from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q

from .decorators import admin_required, role_required
from .services import RoleService
from .models import UserRole, RoleRequest
from dashboard.services import ActivityLogService
from notices.services import NotificationService


@role_required('admin', 'super_admin')
def role_list_view(request: HttpRequest):
    users_with_roles = UserRole.objects.select_related('user', 'approved_by').all()
    context = {
        'users_with_roles': users_with_roles,
        'role_choices': UserRole.ROLE_CHOICES,
    }
    return render(request, 'roles/role_list.html', context)


@role_required('super_admin')
def assign_role_view(request: HttpRequest, user_id: int):
    target_user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        new_role = request.POST.get('role')
        if target_user == request.user:
            messages.error(request, "You cannot change your own role.")
        elif RoleService.can_manage_role(request.user, new_role):
            RoleService.assign_role(target_user, new_role, approved_by=request.user)
            _flush_user_sessions(target_user)
            ActivityLogService.log(
                request.user, f"Assigned role '{new_role}' to {target_user.username}",
                category='role', target_user=target_user, request=request
            )
            messages.success(request, f"Role updated for {target_user.username} to {new_role}")
        else:
            messages.error(request, "You cannot assign a role equal to or above your own.")
        return redirect('roles_list')

    context = {
        'target_user': target_user,
        'role_choices': UserRole.ROLE_CHOICES,
        'current_role': RoleService.get_user_role(target_user),
    }
    return render(request, 'roles/assign_role.html', context)


@admin_required
def pending_approvals_view(request: HttpRequest):
    pending = UserRole.objects.filter(approved=False).select_related('user')
    pending_requests = RoleRequest.objects.filter(status='pending').select_related('user')
    context = {
        'pending_roles': pending,
        'pending_requests': pending_requests,
    }
    return render(request, 'roles/pending_approvals.html', context)


@admin_required
@require_POST
def approve_role_view(request: HttpRequest, role_id: int):
    user_role = get_object_or_404(UserRole, id=role_id)
    action = request.POST.get('action')
    if action == 'approve':
        user_role.approved = True
        user_role.approved_by = request.user
        user_role.save()
        _flush_user_sessions(user_role.user)
        ActivityLogService.log(
            request.user, f"Approved role '{user_role.role}' for {user_role.user.username}",
            category='role', target_user=user_role.user, request=request
        )
        NotificationService.send(
            user_role.user, "Role Approved",
            f"Your role '{user_role.get_role_display()}' has been approved by an admin.",
            notification_type='success'
        )
        messages.success(request, f"Role approved for {user_role.user.username}")
    elif action == 'reject':
        user_role.role = 'user'
        user_role.approved = False
        user_role.save()
        ActivityLogService.log(
            request.user, f"Rejected role for {user_role.user.username}",
            category='role', target_user=user_role.user, request=request
        )
        NotificationService.send(
            user_role.user, "Role Rejected",
            "Your role request was rejected by an admin.",
            notification_type='warning'
        )
        messages.success(request, f"Role request rejected for {user_role.user.username}")
    return redirect('roles_pending')


@login_required
def role_request_view(request: HttpRequest):
    existing_pending = RoleRequest.objects.filter(user=request.user, status='pending').first()
    if existing_pending:
        messages.info(request, "You already have a pending role request.")
        return render(request, 'roles/role_request.html', {'existing': existing_pending})

    if request.method == 'POST':
        requested_role = request.POST.get('requested_role')
        reason = request.POST.get('reason', '').strip()

        if not reason:
            messages.error(request, "Please provide a reason for your request.")
        elif requested_role in ('super_admin',):
            messages.error(request, "You cannot request this role.")
        else:
            RoleRequest.objects.create(
                user=request.user,
                requested_role=requested_role,
                reason=reason,
            )
            ActivityLogService.log(
                request.user, f"Requested role upgrade to '{requested_role}'",
                category='role', request=request
            )
            messages.success(request, "Your role request has been submitted for admin review.")
            return redirect('home')

    available_roles = [r for r in UserRole.ROLE_CHOICES if r[0] not in ('super_admin', 'user')]
    context = {'available_roles': available_roles}
    return render(request, 'roles/role_request.html', context)


@admin_required
@require_POST
def role_request_action_view(request: HttpRequest, request_id: int):
    role_req = get_object_or_404(RoleRequest, id=request_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')

    if action == 'approve':
        role_req.status = 'approved'
        role_req.reviewed_by = request.user
        role_req.review_notes = notes
        role_req.save()
        RoleService.assign_role(role_req.user, role_req.requested_role, approved_by=request.user)
        _flush_user_sessions(role_req.user)
        ActivityLogService.log(
            request.user, f"Approved role request to '{role_req.requested_role}' for {role_req.user.username}",
            category='role', target_user=role_req.user, request=request
        )
        NotificationService.send(
            role_req.user, "Role Request Approved",
            f"Your request for '{role_req.get_requested_role_display()}' role has been approved!",
            notification_type='success'
        )
        messages.success(request, f"Role request approved for {role_req.user.username}")
    elif action == 'reject':
        role_req.status = 'rejected'
        role_req.reviewed_by = request.user
        role_req.review_notes = notes
        role_req.save()
        ActivityLogService.log(
            request.user, f"Rejected role request for {role_req.user.username}",
            category='role', target_user=role_req.user, request=request
        )
        NotificationService.send(
            role_req.user, "Role Request Rejected",
            f"Your request for '{role_req.get_requested_role_display()}' role was rejected.{(' Note: ' + notes) if notes else ''}",
            notification_type='warning'
        )
        messages.success(request, f"Role request rejected for {role_req.user.username}")

    return redirect('roles_pending')


@admin_required
def members_directory_view(request: HttpRequest):
    search = request.GET.get('q', '').strip()[:100]
    role_filter = request.GET.get('role', '')

    members = UserRole.objects.select_related('user', 'user__profile').filter(approved=True)

    if search:
        members = members.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )
    if role_filter:
        members = members.filter(role=role_filter)

    paginator = Paginator(members.order_by('-created_at'), 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page': page,
        'search': search,
        'role_filter': role_filter,
        'role_choices': UserRole.ROLE_CHOICES,
    }
    return render(request, 'roles/members_directory.html', context)


@admin_required
@require_POST
def toggle_user_active_view(request: HttpRequest, user_id: int):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('members_directory')
    if target_user.is_superuser:
        messages.error(request, "Cannot deactivate a superuser account.")
        return redirect('members_directory')

    target_user.is_active = not target_user.is_active
    target_user.save()
    if not target_user.is_active:
        _flush_user_sessions(target_user)
    status = "activated" if target_user.is_active else "deactivated"
    ActivityLogService.log(
        request.user, f"{status.capitalize()} user account: {target_user.username}",
        category='role', target_user=target_user, request=request
    )
    NotificationService.send(
        target_user, f"Account {status.capitalize()}",
        f"Your account has been {status} by an administrator.",
        notification_type='success' if target_user.is_active else 'warning'
    )
    messages.success(request, f"User {target_user.username} has been {status}.")
    return redirect('members_directory')


def _flush_user_sessions(user):
    """Delete all active sessions belonging to a specific user."""
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions.iterator():
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.pk):
            session.delete()
