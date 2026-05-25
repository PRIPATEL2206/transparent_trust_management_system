from django.http import HttpRequest
from django.shortcuts import render
from django.contrib.auth.decorators import login_not_required
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from .services import TransparencyService


@login_not_required
@cache_page(60 * 5)
@vary_on_cookie
def transparency_view(request: HttpRequest):
    context = {
        'donation_summary': TransparencyService.get_donation_summary(),
        'expense_summary': TransparencyService.get_expense_summary(),
        'fund_flow': TransparencyService.get_fund_flow(),
        'ngo_summary': TransparencyService.get_ngo_funding_summary(),
        'monthly_breakdown': TransparencyService.get_monthly_breakdown(),
        'recent_donations': TransparencyService.get_recent_approved_donations(),
    }
    return render(request, 'transparency/transparency.html', context)
