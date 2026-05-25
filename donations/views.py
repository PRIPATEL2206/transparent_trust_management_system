from django.http.request import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, login_not_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page
from django.db.models import Q

from roles.decorators import admin_required
from a_customeauth.decorators import email_verified_required
from dashboard.services import ActivityLogService
from notices.services import NotificationService
from services.csv_utils import make_csv_response
from services.pagination import safe_paginate
from services.rate_limit import rate_limit
from .forms import AddDonationForm, AddDonationTypeForm
from .models import DonationType, Donation


@login_not_required
@cache_page(60 * 2)
def donation_type_page_view(request:HttpRequest):
    context={
        'donation_types':DonationType.objects.all().order_by('-starting_date')
    }
    return render(request,'donations/all_donations.html',context)

@login_not_required
def donation_page_view(request:HttpRequest,id:str):
    search = request.GET.get('search',"")[:100]
    sort_by = request.GET.get('sort_by',"created_at")

    donation_type = get_object_or_404(DonationType, id=int(id))

    allowed_sorts = ('created_at', 'amount', 'display_name')
    if sort_by not in allowed_sorts:
        sort_by = 'created_at'

    donations = Donation.objects.filter(
        Q(donation_for=id) & Q(is_approved=True) & (
            Q(display_name__icontains=search) |
            Q(handover_by__icontains=search) |
            Q(desc__icontains=search) |
            Q(add_by__username__icontains=search)
        )
    ).select_related('add_by', 'donation_for').order_by("-"+sort_by)
    page, paginator = safe_paginate(donations, request)

    context={
        'page':page,
        'donation_type':donation_type,
        "total":paginator.count,
        "total_pages":paginator.num_pages,
        "search":search,
        "sort_by":sort_by
    }

    return render(request,'donations/donations.html',context)

@login_required
def add_donation_types(request:HttpRequest):
    form = AddDonationTypeForm()
    if request.POST:
        form = AddDonationTypeForm(request.POST,request.FILES)
        if form.is_valid():
            donation_type = form.save(commit=False)
            donation_type.created_by = request.user
            donation_type.save()
            form = AddDonationTypeForm()

    context = {
        'form':form,
        'title':"Add Doantion Type"
    }
    return render(request,'donations/add_page.html',context)

@login_required
@email_verified_required
def add_donation(request:HttpRequest):
    donation_type = request.GET.get('type')
    form = AddDonationForm({"donation_for":donation_type})
    form.errors.clear()
    if request.POST:
        form = AddDonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.add_by = request.user
            donation.is_approved = False
            donation.save()
            ActivityLogService.log(
                request.user, f"Added donation of ₹{donation.amount} ({donation.display_name})",
                category='donation', request=request
            )
            messages.success(request, "Donation submitted for admin approval.")
            return redirect('donations_types')

    context = {
        'form':form,
        'title':"Add Donations"
        }
    return render(request,'donations/add_page.html',context)


@admin_required
def donation_admin_view(request: HttpRequest):
    status = request.GET.get('status', 'pending')
    if status == 'pending':
        donations = Donation.objects.filter(is_approved=False).select_related('add_by', 'donation_for')
    else:
        donations = Donation.objects.filter(is_approved=True).select_related('add_by', 'donation_for')

    page, _ = safe_paginate(donations.order_by('-created_at'), request, default_per_page=15)
    context = {'page': page, 'status': status}
    return render(request, 'donations/donation_admin.html', context)


@admin_required
@require_POST
def donation_action_view(request: HttpRequest, donation_id: int):
    donation = get_object_or_404(Donation, id=donation_id)
    action = request.POST.get('action')
    if action == 'approve':
        donation.is_approved = True
        donation.save()
        ActivityLogService.log(
            request.user, f"Approved donation of ₹{donation.amount} by {donation.add_by.username}",
            category='donation', target_user=donation.add_by, request=request
        )
        NotificationService.send(
            donation.add_by, "Donation Approved",
            f"Your donation of ₹{donation.amount} ({donation.display_name}) has been approved.",
            notification_type='success', link='/donation/'
        )
        messages.success(request, "Donation approved.")
    elif action == 'reject':
        donation.delete()
        ActivityLogService.log(
            request.user, f"Rejected donation by {donation.add_by.username}",
            category='donation', target_user=donation.add_by, request=request
        )
        NotificationService.send(
            donation.add_by, "Donation Rejected",
            f"Your donation entry '{donation.display_name}' was rejected by an admin.",
            notification_type='warning'
        )
        messages.success(request, "Donation rejected and removed.")
    return redirect('donations_admin')


@admin_required
@rate_limit(max_attempts=5, window=300, key_prefix='donation_export')
def donation_export_view(request: HttpRequest):
    donations = Donation.objects.select_related('add_by', 'donation_for').filter(is_approved=True).order_by('-created_at')[:10000]

    rows = [
        [
            d.display_name, d.amount,
            d.donation_for.name if d.donation_for else '',
            d.add_by.username, d.handover_by,
            d.created_at.strftime('%Y-%m-%d'),
            'Yes' if d.is_approved else 'No',
        ]
        for d in donations
    ]
    return make_csv_response(
        'donations_export.csv',
        ['Display Name', 'Amount', 'Type', 'Added By', 'Handover By', 'Date', 'Approved'],
        rows
    )