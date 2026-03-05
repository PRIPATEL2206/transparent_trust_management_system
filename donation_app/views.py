from django.conf import settings # new
from django.shortcuts import render,redirect
from django.views.generic import FormView
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
        print('donation created before jcidji')
        # donation: Donation = form.save(commit=False)
        # donation.campaign = self.campaign
        # donation.donor = self.request.user if self.request.user.is_authenticated else None
        # donation.save()
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
                    'intended_currency': 'INR',
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
                        'currency': 'INR',
                        'product_data': {
                            'name':campaign.title,
                            'description': 'Donation for campaign'+campaign.title,
                        },
                        # 'metadata': {
                        #     'campaign_id': str(campaign.id),
                        #     'donor_id': str(donor.id),
                        # },
                        'unit_amount': int(amount*1000),
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
    
