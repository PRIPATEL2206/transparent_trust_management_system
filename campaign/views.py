from django.shortcuts import render
from .form import CampaignForm
from django.views.generic import View,ListView
from .models import Campaign,CampaignImages,CampaignCategory
from django.shortcuts import render, redirect
from django.contrib import messages
from account.decorators import email_verification_required
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.core.paginator import Paginator

from request_app.models import RequestStatus



# Create your views here.
@method_decorator(email_verification_required, name='dispatch')
class CreateCampaignView(View):
    template_name = "campaign/create.html"

    def get(self, request):
        return render(request, self.template_name,{'form':CampaignForm()})

    def post(self, request):
        form = CampaignForm(request.POST, request.FILES)
        if form.is_valid():
            campaign = form.save(request.user)
            messages.success(request, "campais request sended successfully")

        return render(request, self.template_name, {"form": form})

@method_decorator(email_verification_required, name='dispatch')
class CampaignListView(ListView):
    model = Campaign
    template_name = "campaign/list.html"
    context_object_name = "object_list"  # keeps the same name you used
    paginate_by = 10  # default; we'll override dynamically
    ordering = "title"  # default sort

    # Map friendly sort keys to model fields
    SORT_MAP = {
        "title": "title",
        "category": "category__name",
        "status": "status",
        "start_date": "start_date",
        "end_date": "end_date",
        "goal_amount": "goal_amount",
    }

    def get_queryset(self):
        request = self.request
        q = request.GET.get("q", "").strip()
        status = request.GET.get("status", "").strip()
        sort = request.GET.get("sort", "title").strip()
        direction = request.GET.get("dir", "asc").strip().lower()  # 'asc' or 'desc'

        # Base queryset with select_related/only for efficiency
        qs = (
            Campaign.objects.select_related("category")
            .only(
                "id", "title", "slug", "request__status", "start_date", "end_date",
                "goal_amount", "cover_image", "category__name"
            )
        )
        if not request.user.is_approval_user:
            qs = qs.filter(Q(request__proposed_by=request.user))

        # Search (title, short_description, description, category name, status)
        if q:
            qs = qs.filter(
                Q(slug__icontains=q)
                | Q(title__icontains=q)
                | Q(short_description__icontains=q)
                | Q(description__icontains=q)
                | Q(category__name__icontains=q)
                | Q(request__status__icontains=q)
            )
            # If you want to include tags (JSONField) and you're on PostgreSQL:
            # qs = qs.filter(Q(tags__icontains=q) | Q(...existing...))

        # Filter by status (ensure values match your CampaignStatus choices)
        if status:
            qs = qs.filter(request__status=status)

        # Sorting
        sort_field = self.SORT_MAP.get(sort, "title")
        if direction == "desc":
            sort_field = f"-{sort_field}"
        qs = qs.order_by(sort_field)

        return qs

    def get_paginate_by(self, queryset):
        """
        Dynamically determine page size with clamping: 1..100
        """
        page_size = self.request.GET.get("page_size", "10")
        try:
            page_size = min(max(int(page_size), 1), 100)
        except ValueError:
            page_size = 10
        return page_size

    def get_context_data(self, **kwargs):
        """
        Add the same context fields you had in your FBV.
        """
        context = super().get_context_data(**kwargs)
        request = self.request

        q = request.GET.get("q", "").strip()
        status_value = request.GET.get("status", "").strip()
        sort = request.GET.get("sort", "title").strip()
        direction = request.GET.get("dir", "asc").strip().lower()

        # Ensure paginator/page_obj are available (ListView handles this)
        # But we also expose `paginator` explicitly as you did
        context.update({
            "q": q,
            "status_value": status_value,
            "sort": sort,
            "dir": direction,
            "page_size": self.get_paginate_by(self.get_queryset()),
            "paginator": context.get("paginator"),
            "page_obj": context.get("page_obj"),
            # "object_list" is already provided as per context_object_name
        })
        context['RequestStatus']=RequestStatus
        return context
