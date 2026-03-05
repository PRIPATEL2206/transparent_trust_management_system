from decimal import Decimal
from django.shortcuts import render
from django.views.generic import TemplateView
import stripe
from django.conf import settings 
from .models import Payment,PaymentStatus,PaymentFor
from django.shortcuts import get_object_or_404
from donation_app import models as donation_models
from campaign.models import Campaign
from account.models import CustomUser



# Create your views here.
# class PaymentCreateView(View):
#     def post(self, request):
#         amount = request.POST.get('amount')
#         stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentSuccessView(TemplateView):
    template_name = 'payment_app/success.html'

    def get(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session_id = request.GET.get('session_id')
        if not session_id:
            # handle error gracefully
            return super().get(request)
        payment=get_object_or_404(Payment,payment_id=session_id)
        session = stripe.checkout.Session.retrieve(session_id)
        session_meta = session.get('metadata', {})
        payment.status=PaymentStatus.SUCCESS
        payment.save()
        if payment.payment_for==PaymentFor.DONATIONS:
            donation_models.Donation.objects.create(
                campaign=get_object_or_404(Campaign,id=session_meta.get('campaign_id')),
                donor=get_object_or_404(CustomUser,id=session_meta.get('donor_id')),
                amount=Decimal(session_meta.get('intended_amount')),
                currency=session_meta.get('intended_currency'),
                dispaly_name=session_meta.get('display_name'),
                donor_display_name=session_meta.get('display_name'),
                description=session_meta.get('note'),
                payment=payment
            )

        print("Session metadata:", session_meta)
        return super().get(request, *args, **kwargs)

class PaymentCancelledView(TemplateView):
    template_name = 'payment_app/cancelled.html'