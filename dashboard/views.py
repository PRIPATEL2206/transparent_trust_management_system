from django.http import HttpRequest
from django.shortcuts import render

from roles.decorators import role_required
from services.csv_utils import make_csv_response
from services.pagination import safe_paginate
from services.rate_limit import rate_limit
from .services import DashboardService, ActivityLogService


@role_required('admin', 'super_admin')
def dashboard_view(request: HttpRequest):
    context = {
        'donation_stats': DashboardService.get_donation_stats(),
        'expense_stats': DashboardService.get_expense_stats(),
        'transaction_stats': DashboardService.get_transaction_stats(),
        'user_stats': DashboardService.get_user_stats(),
        'recent_activity': DashboardService.get_recent_activity(),
        'monthly_summary': DashboardService.get_monthly_summary(),
        'activity_logs': ActivityLogService.get_recent(limit=10),
        'breadcrumbs': [{'label': 'Dashboard'}],
    }
    return render(request, 'dashboard/dashboard.html', context)


@role_required('admin', 'super_admin')
def activity_log_view(request: HttpRequest):
    from .models import ActivityLog
    logs = ActivityLog.objects.select_related('user', 'target_user').all()
    category = request.GET.get('category', '')
    if category:
        logs = logs.filter(category=category)
    page, _ = safe_paginate(logs, request, default_per_page=25)
    context = {
        'page': page,
        'category': category,
        'categories': ActivityLog.CATEGORY_CHOICES,
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/dashboard/'},
            {'label': 'Activity Log'},
        ],
    }
    return render(request, 'dashboard/activity_log.html', context)


@role_required('admin', 'super_admin')
@rate_limit(max_attempts=5, window=300, key_prefix='activity_export')
def activity_log_export_view(request: HttpRequest):
    from .models import ActivityLog
    logs = ActivityLog.objects.select_related('user', 'target_user').order_by('-created_at')
    category = request.GET.get('category', '')
    if category:
        logs = logs.filter(category=category)
    logs = logs[:5000]

    rows = [
        [
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else 'system',
            log.get_category_display(),
            log.action,
            log.target_user.username if log.target_user else '',
            log.ip_address or '',
        ]
        for log in logs
    ]
    return make_csv_response(
        'activity_log_export.csv',
        ['Timestamp', 'User', 'Category', 'Action', 'Target User', 'IP Address'],
        rows
    )
