# views.py
from decimal import Decimal
from django.db.models import Q, Sum, Count, F
from django.db.models.functions import Coalesce
from django.db.models.expressions import OrderBy
from django.utils import timezone
from django.views.generic import ListView, DetailView, FormView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from .models import Campaign, CampaignCategory
from donation_app.form import DonationForm

class CampaignListView(ListView):
    model = Campaign
    template_name = "campaign/public_list.html"
    context_object_name = "campaigns"
    paginate_by = 12

    def get_queryset(self):
        qs = Campaign.objects.all().select_related("category").prefetch_related("gallery")

        # Only public + currently active (adjust if your logic differs)
        now = timezone.now()
        qs = qs.filter(
            visibility="PUBLIC",                     # or Visibility.PUBLIC if using enum
            start_date__lte=now
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=now))

        # Search
        q = (self.request.GET.get("q") or "").strip()
        if q:
            terms = [t for t in q.split() if t]
            for t in terms:
                qs = qs.filter(
                    Q(title__icontains=t) |
                    Q(short_description__icontains=t) |
                    Q(description__icontains=t) |
                    Q(category__name__icontains=t) |
                    Q(tags__icontains=t)  # JSONField contains text (works on Postgres & SQLite icontains)
                )

        # Optional: category filter
        cat_id = self.request.GET.get("category")
        if cat_id:
            qs = qs.filter(category_id=cat_id)

        # Annotate for sorting and card stats
        qs = qs.annotate(
            _amount_raised=Coalesce(Sum("donations__amount"), Decimal("0.00")),
            _donations_count=Coalesce(Count("donations", distinct=True), 0),
        )

        # Sorting map
        sort = (self.request.GET.get("sort") or "").lower()
        order_map = {
            "new":      [OrderBy(F("start_date"), descending=True)],
            "end_soon": [OrderBy(F("end_date"), descending=False, nulls_last=True)],
            "goal_high":[OrderBy(F("goal_amount"), descending=True,  nulls_last=True)],
            "goal_low": [OrderBy(F("goal_amount"), descending=False, nulls_last=True)],
            "raised_high":[OrderBy(F("_amount_raised"), descending=True)],
            "raised_low": [OrderBy(F("_amount_raised"), descending=False)],
            "popular":  [OrderBy(F("_donations_count"), descending=True)],
            "title_az": [OrderBy(F("title"), descending=False)],
            "title_za": [OrderBy(F("title"), descending=True)],
        }
        ordering = order_map.get(sort) or [OrderBy(F("start_date"), descending=True)]
        return qs.order_by(*ordering)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["sort"] = self.request.GET.get("sort", "")
        ctx["selected_category"] = self.request.GET.get("category", "")
        ctx["categories"] = CampaignCategory.objects.all().order_by("name")
        # Keep existing filters in pagination links
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["querystring"] = params.urlencode()
        return ctx


class CampaignDetailView(DetailView):
    model = Campaign
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "campaign/detail.html"
    context_object_name = "campaign"

    def get_queryset(self):
        now = timezone.now()
        return (
            Campaign.objects.select_related("category")
            .prefetch_related("gallery")
            .annotate(
                _amount_raised=Coalesce(Sum("donations__amount"), Decimal("0.00")),
                _donations_count=Coalesce(Count("donations", distinct=True), 0),
            )
            .filter(
                visibility="PUBLIC",
                start_date__lte=now
            )
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=now))
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["donation_form"] = DonationForm(campaign=self.object)
        return ctx
