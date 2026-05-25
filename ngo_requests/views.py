from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from roles.decorators import role_required, admin_required
from dashboard.services import ActivityLogService
from notices.services import NotificationService
from .models import FundRequest
from .forms import FundRequestForm
from .services import NGOFundService


@role_required('ngo')
def fund_request_list_view(request: HttpRequest):
    requests = NGOFundService.get_ngo_requests(request.user)
    paginator = Paginator(requests, 10)
    page = paginator.get_page(request.GET.get('page', 1))
    context = {'page': page}
    return render(request, 'ngo_requests/request_list.html', context)


@role_required('ngo')
def fund_request_create_view(request: HttpRequest):
    form = FundRequestForm()
    if request.method == 'POST':
        form = FundRequestForm(request.POST, request.FILES)
        if form.is_valid():
            NGOFundService.create_request(
                user=request.user,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                amount=form.cleaned_data['amount_requested'],
                documents=form.cleaned_data.get('supporting_documents')
            )
            ActivityLogService.log(
                request.user, f"Submitted fund request: {form.cleaned_data['title']}",
                category='ngo', request=request
            )
            messages.success(request, "Fund request submitted for review.")
            return redirect('ngo_requests_list')
    return render(request, 'ngo_requests/request_form.html', {'form': form})


@admin_required
def fund_request_admin_view(request: HttpRequest):
    pending = NGOFundService.get_pending_requests()
    all_requests = FundRequest.objects.select_related('ngo_user', 'reviewed_by').order_by('-created_at')
    paginator = Paginator(all_requests, 20)
    page = paginator.get_page(request.GET.get('page', 1))
    context = {'pending': pending, 'page': page}
    return render(request, 'ngo_requests/request_admin.html', context)


@admin_required
@require_POST
def fund_request_action_view(request: HttpRequest, request_id: int):
    fund_request = get_object_or_404(FundRequest, id=request_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')

    if action == 'approve':
        amount = request.POST.get('amount_approved', fund_request.amount_requested)
        NGOFundService.approve_request(fund_request, request.user, float(amount), notes)
        ActivityLogService.log(
            request.user, f"Approved fund request '{fund_request.title}' (₹{amount})",
            category='ngo', target_user=fund_request.ngo_user, request=request
        )
        NotificationService.send(
            fund_request.ngo_user, "Fund Request Approved",
            f"Your fund request '{fund_request.title}' has been approved for ₹{amount}.",
            notification_type='success', link='/ngo-requests/'
        )
        messages.success(request, "Fund request approved.")
    elif action == 'reject':
        NGOFundService.reject_request(fund_request, request.user, notes)
        ActivityLogService.log(
            request.user, f"Rejected fund request '{fund_request.title}'",
            category='ngo', target_user=fund_request.ngo_user, request=request
        )
        NotificationService.send(
            fund_request.ngo_user, "Fund Request Rejected",
            f"Your fund request '{fund_request.title}' was rejected.{(' Reason: ' + notes) if notes else ''}",
            notification_type='warning', link='/ngo-requests/'
        )
        messages.success(request, "Fund request rejected.")
    elif action == 'disburse':
        NGOFundService.mark_disbursed(fund_request, request.user)
        ActivityLogService.log(
            request.user, f"Disbursed funds for '{fund_request.title}'",
            category='ngo', target_user=fund_request.ngo_user, request=request
        )
        NotificationService.send(
            fund_request.ngo_user, "Funds Disbursed",
            f"Funds for your request '{fund_request.title}' have been disbursed.",
            notification_type='success', link='/ngo-requests/'
        )
        messages.success(request, "Funds marked as disbursed.")

    return redirect('ngo_requests_admin')
