from django.shortcuts import render
from django.views.generic import FormView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from campaign.models import Campaign
from donation_app.models import Donation
from . import form
# Create your views here.

class DonationCreateView(FormView):
    form_class = form.DonationForm
    template_name = "campaigns/donate_inline.html"

    def get_success_url(self):
        return self.request.META.get("HTTP_REFERER") or self.request.path


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
        donation: Donation = form.save(commit=False)
        donation.campaign = self.campaign
        donation.donor = self.request.user if self.request.user.is_authenticated else None
        donation.save()
        return redirect(self.campaign.get_absolute_url() + "?thanks=1")