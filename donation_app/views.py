from django.conf import settings # new
from django.shortcuts import render,redirect
from django.views.generic import FormView,ListView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
import stripe
import json

from campaign.models import Campaign
from donation_app.models import Donation
from payment_app import models as payment_models
from . import form
from .form import DonationFilterForm
# Create your views here.

class DonationCreateView(FormView):
    form_class = form.DonationForm
    template_name = "donation_app/donate_inline.html"

    def get_success_url(self):
        return self.request.META.get("HTTP_REFERER") or self.request.path

    def form_invalid(self, form):
        print('form invalid')
        print(form.errors)
        print(form.errors.as_data())
        print(form.errors.as_json())

        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        now = timezone.now()
        self.campaign = get_object_or_404(
            Campaign.objects.filter(
                visibility="PUBLIC",
                start_date__lte=now
            ).filter(Q(end_date__isnull=True) | Q(end_date__gte=now)),
            slug=slug,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["campaign"] = self.campaign
        return kwargs

    def form_valid(self, form):
        campaign=self.campaign
        amount=float(form.cleaned_data['amount'])
        currency=form.cleaned_data['currency']
        dispaly_name=form.cleaned_data['donor_display_name']
        description=form.cleaned_data['description']
        donor=self.request.user if self.request.user and self.request.user.is_authenticated else None

        try:
            domain_url = 'https://8000-firebase-trustmanagement-1767157773363.cluster-udxxdyopu5c7cwhhtg6mmadhvs.cloudworkstations.dev/payment/'
            stripe.api_key = settings.STRIPE_SECRET_KEY
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + 'success/?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancelled/',
                payment_method_types=['card'],
                mode='payment',
                metadata={
                    'campaign_id': str(campaign.id),
                    'donor_id': str(donor.id),
                    'display_name': dispaly_name,  # keeping your variable name
                    'note': description or '',
                    'intended_amount': str(amount),
                    'intended_currency': currency,
                },         
                payment_intent_data={
                    'metadata': {
                        'campaign_id': str(campaign.id),
                        'donor_id': str(donor.id),
                        'display_name': dispaly_name,
                        'note': description or '',
                    }
                },
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name':campaign.title,
                            'description': 'Donation for campaign'+campaign.title,
                        },
                        'unit_amount': int(amount*100),
                    },
                    'quantity': 1,
                    }],
                )
            
            payment=payment_models.Payment.objects.create(
                user=donor,
                payment_id=checkout_session.id,
                amount=amount,    
                status=payment_models.PaymentStatus.PENDING,
                payment_for=payment_models.PaymentFor.DONATIONS
            )
            # return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

        return redirect(checkout_session.url)

class DonationListView(ListView):
    model = Donation
    template_name = "donations/donation_list.html"
    context_object_name = "donations"
    paginate_by = 25

    def get_ordering(self):
        # Map safe ordering aliases to actual model fields
        ordering_param = self.request.GET.get('ordering') or '-created'
        mapping = {
            'created': 'created_at',
            '-created': '-created_at',
            'amount': 'amount',
            '-amount': '-amount',
        }
        return mapping.get(ordering_param, '-created_at')

    def get_queryset(self):
        qs = (
            Donation.objects
            .select_related('campaign', 'donor', 'payment')
            .all()
        )

        self.filter_form = DonationFilterForm(self.request.GET or None)
        if self.filter_form.is_valid():
            cd = self.filter_form.cleaned_data

            if cd.get('campaign'):
                qs = qs.filter(campaign=cd['campaign'])

            if cd.get('category'):
                qs = qs.filter(campaign__category=cd['category'])

            if cd.get('donor'):
                qs = qs.filter(donor=cd['donor'])

            if cd.get('currency'):
                qs = qs.filter(currency=cd['currency'])

            if cd.get('visibility'):
                qs = qs.filter(campaign__visibility=cd['visibility'])

            if cd.get('amount_min') is not None:
                qs = qs.filter(amount__gte=cd['amount_min'])

            if cd.get('amount_max') is not None:
                qs = qs.filter(amount__lte=cd['amount_max'])

            if cd.get('created_from'):
                qs = qs.filter(created_at__date__gte=cd['created_from'])

            if cd.get('created_to'):
                qs = qs.filter(created_at__date__lte=cd['created_to'])

            if cd.get('has_payment'):
                has_payment = cd['has_payment']
                if has_payment == '1':
                    qs = qs.filter(payment__isnull=False)
                elif has_payment == '0':
                    qs = qs.filter(payment__isnull=True)

            # Search in several text fields``
            if cd.get('q'):
                q = cd['q'].strip()
                qs = qs.filter(
                    Q(campaign__title__icontains=q) |
                    Q(description__icontains=q) |
                    Q(donor_display_name__icontains=q) |
                    Q(dispaly_name__icontains=q)  # using your field name as-is
                )

            # Tags: if you store tags as list in JSONField, contains works with subsets.
            # For "any tag matches", OR the filters.
            if cd.get('tags'):
                tags_list = [t.strip() for t in cd['tags'].split(',') if t.strip()]
                if tags_list:
                    tag_q = Q()
                    for t in tags_list:
                        # Match list containing a single value t
                        tag_q |= Q(campaign__tags__contains=[t])
                    qs = qs.filter(tag_q)

        # Apply ordering (defaults to -created_at)
        qs = qs.order_by(self.get_ordering())
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = self.filter_form
        # Aggregates for the current (filtered) queryset in this page or overall:
        full_qs = self.get_queryset().values('id')  # avoid re-evaluating heavy annotations
        # Better approach to avoid double query: compute on paginator.object_list; here, a quick demo:
        from django.db.models import Sum
        ctx['total_amount'] = self.object_list.aggregate(total=Sum('amount'))['total'] or 0
        ctx['ordering'] = self.request.GET.get('ordering') or '-created'
        return ctx