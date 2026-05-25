from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from roles.decorators import role_required, admin_required
from a_customeauth.decorators import email_verified_required
from dashboard.services import ActivityLogService
from notices.services import NotificationService
from services.csv_utils import make_csv_response
from services.pagination import safe_paginate
from services.rate_limit import rate_limit
from .models import Expense
from .forms import ExpenseForm
from .services import ExpenseService


@login_required
def expense_list_view(request: HttpRequest):
    expenses = ExpenseService.get_user_expenses(request.user)
    status_filter = request.GET.get('status', '')
    if status_filter:
        expenses = expenses.filter(status=status_filter)
    page, _ = safe_paginate(expenses, request)
    context = {'page': page, 'status': status_filter}
    return render(request, 'expenses/expense_list.html', context)


@login_required
@email_verified_required
def expense_create_view(request: HttpRequest):
    form = ExpenseForm()
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            ExpenseService.create_expense(
                user=request.user,
                title=data['title'],
                description=data['description'],
                amount=data['amount'],
                category=data['category'],
                receipt=data.get('receipt')
            )
            messages.success(request, "Expense created successfully.")
            return redirect('expenses_list')
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Create Expense'})


@login_required
@require_POST
def expense_submit_view(request: HttpRequest, expense_id: int):
    expense = get_object_or_404(Expense, id=expense_id, raised_by=request.user)
    ExpenseService.submit_for_approval(expense, request.user)
    messages.success(request, "Expense submitted for approval.")
    return redirect('expenses_list')


@admin_required
def expense_admin_list_view(request: HttpRequest):
    status = request.GET.get('status', 'pending')
    expenses = Expense.objects.filter(status=status).select_related('raised_by', 'category').order_by('-created_at')
    page, _ = safe_paginate(expenses, request)
    context = {'page': page, 'status': status}
    return render(request, 'expenses/expense_admin_list.html', context)


@admin_required
@require_POST
def expense_action_view(request: HttpRequest, expense_id: int):
    expense = get_object_or_404(Expense, id=expense_id)
    action = request.POST.get('action')
    if action == 'approve':
        ExpenseService.approve_expense(expense, request.user)
        ActivityLogService.log(
            request.user, f"Approved expense '{expense.title}' (₹{expense.amount})",
            category='expense', target_user=expense.raised_by, request=request
        )
        NotificationService.send(
            expense.raised_by, "Expense Approved",
            f"Your expense '{expense.title}' (₹{expense.amount}) has been approved.",
            notification_type='success', link='/expenses/'
        )
        messages.success(request, "Expense approved.")
    elif action == 'reject':
        reason = request.POST.get('reason', '')
        ExpenseService.reject_expense(expense, request.user, reason)
        ActivityLogService.log(
            request.user, f"Rejected expense '{expense.title}'",
            category='expense', target_user=expense.raised_by, request=request
        )
        NotificationService.send(
            expense.raised_by, "Expense Rejected",
            f"Your expense '{expense.title}' was rejected.{(' Reason: ' + reason) if reason else ''}",
            notification_type='warning', link='/expenses/'
        )
        messages.success(request, "Expense rejected.")
    elif action == 'mark_paid':
        ExpenseService.mark_paid(expense, request.user)
        ActivityLogService.log(
            request.user, f"Marked expense '{expense.title}' as paid",
            category='expense', target_user=expense.raised_by, request=request
        )
        NotificationService.send(
            expense.raised_by, "Expense Paid",
            f"Your expense '{expense.title}' (₹{expense.amount}) has been marked as paid.",
            notification_type='success', link='/expenses/'
        )
        messages.success(request, "Expense marked as paid.")
    return redirect('expenses_admin_list')


@admin_required
@rate_limit(max_attempts=5, window=300, key_prefix='expense_export')
def expense_export_view(request: HttpRequest):
    status = request.GET.get('status', '')
    expenses = Expense.objects.select_related('raised_by', 'category').order_by('-created_at')
    if status:
        expenses = expenses.filter(status=status)
    expenses = expenses[:10000]

    rows = [
        [
            e.title, e.amount,
            e.category.name if e.category else '',
            e.get_status_display(),
            e.raised_by.username,
            e.created_at.strftime('%Y-%m-%d'),
        ]
        for e in expenses
    ]
    return make_csv_response(
        f'expenses_{status or "all"}.csv',
        ['Title', 'Amount', 'Category', 'Status', 'Raised By', 'Date'],
        rows
    )
