from django.shortcuts import render,redirect
from django.views.generic import DetailView,CreateView,UpdateView,ListView
from django.db.models import Q
from django.contrib import messages
from django.utils.decorators import method_decorator
from account.decorators import email_verification_required

from . import models,form


# Create your views here.
@method_decorator(email_verification_required, name='dispatch')
class RequestDetailView(DetailView):
    model = models.Request
    template_name = "request/detail.html"
    context_object_name = "request_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_obj = self.get_object()

        available_options = {}
        if request_obj.can_approve(self.request.user):
            available_options['APPROVED'] = 'Approve'
        if request_obj.can_reject(self.request.user):
            available_options['REJECTED'] = 'Reject'
        if request_obj.can_cancel(self.request.user):
            available_options['CANCELED'] = 'Cancel'
        if request_obj.can_send_for_review(self.request.user):
            print("-----------------","can reiwew")
            available_options['PENDING_REVIEW'] = 'Send for Review'
        if request_obj.can_draft(self.request.user):
            available_options['DRAFT'] = 'Draft'
        context['available_options'] = available_options
        context['can_chat'] = request_obj.can_chat(self.request.user) 
        context['req_messages'] = request_obj.messages.all()
        context['form'] = form.RequestMessageForm(self.request.POST)
        context['back_url'] = self.request.META.get('HTTP_REFERER') or self.request.path
        return context

@method_decorator(email_verification_required, name='dispatch')
class RequestMessageCreateView(CreateView):
    model = models.RequestMessage
    form_class = form.RequestMessageForm

    def post(self,request,pk,*args,**kwargs):  
        requestMassge=models.RequestMessage.objects.create(sender=request.user,request=models.Request.objects.get(pk=pk),massges=request.POST.get('massges'))
        return redirect('request_app:detail',pk=pk)

@method_decorator(email_verification_required, name='dispatch')
class RequestUpdateStatusView(UpdateView):
    model = models.Request
    fields = ['status']
    http_method_names = ['post']

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER') or self.request.path
    def post(self,request,*args,**kwargs):
        try:
            req_object =self.get_object()
            print(request.POST.get('status'))
            switcher = {
                models.RequestStatus.APPROVED: req_object.approve,
                models.RequestStatus.CANCELED: req_object.cancel,
                models.RequestStatus.REJECTED: req_object.reject,
                models.RequestStatus.PENDING_REVIEW: req_object.send_for_review,
                models.RequestStatus.DRAFT: req_object.send_for_draft
            }
            switcher[request.POST.get('status')](request.user)
            messages.success(request, "Updated successfully")
        except AttributeError:
            messages.error(request, "Invalid action")
        except KeyError:
            messages.error(request, "Invalid action")
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.get_success_url())

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, "Updated successfully")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        # Include form errors in the message if useful
        messages.error(self.request, f"Update failed: {form.errors.as_text()}")
        return redirect(self.get_success_url())

@method_decorator(email_verification_required, name='dispatch')
class RequestListView(ListView):
    model = models.Request
    template_name = "request/list.html"
    context_object_name = "object_list"  # keeps the same name you used
    paginate_by = 10  # default; we'll override dynamically
    ordering = "last_updated"  # default sort

    # Map friendly sort keys to model fields
    SORT_MAP = {
        "requested_for": "requested_for",
        "status": "status",
        "start_date": "start_date",
        "last_updated": "last_updated",
    }

    def get_queryset(self):
        request = self.request
        q = request.GET.get("q", "").strip()
        status = request.GET.get("status", "").strip()
        sort = request.GET.get("sort", self.ordering).strip()
        direction = request.GET.get("dir", "asc").strip().lower()  # 'asc' or 'desc'

        # Base queryset with select_related/only for efficiency
        qs = (
            models.Request.objects.select_related("proposed_by", "reviewed_by")
            .only(
                "requested_for","status","start_date","last_updated","reviewed_by__first_name","reviewed_by__middel_name","reviewed_by__last_name","proposed_by__first_name","proposed_by__middel_name","proposed_by__last_name"
            )
        )
        if not request.user.is_approval_user:
            qs = qs.filter(Q(proposed_by=request.user))
        else:
            qs = qs.filter(~Q(status=models.RequestStatus.DRAFT))


        # Search (title, short_description, description, category name, status)
        if q:
            qs = qs.filter(
                Q(proposed_by__first_name__icontains=q)
                | Q(proposed_by__middel_name__icontains=q)
                | Q(proposed_by__last_name__icontains=q)
                | Q(reviewed_by__first_name__icontains=q)
                | Q(reviewed_by__middel_name__icontains=q)
                | Q(reviewed_by__last_name__icontains=q)
                
                | Q(status__icontains=q)
                | Q(requested_for__icontains=q)
            )
            # If you want to include tags (JSONField) and you're on PostgreSQL:
            # qs = qs.filter(Q(tags__icontains=q) | Q(...existing...))

        # Filter by status (ensure values match your CampaignStatus choices)
        if status:
            qs = qs.filter(status=status)

        # Sorting
        sort_field = self.SORT_MAP.get(sort, self.ordering)
        if direction == "desc":
            sort_field = f"-{sort_field}"
        qs = qs.order_by(sort_field)

        return qs

    def get_paginate_by(self, queryset):
        """
        Dynamically determine page size with clamping: 1..100
        """
        page_size = self.request.GET.get("page_size", f"{self.paginate_by}")
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
        sort = request.GET.get("sort", self.ordering).strip()
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
        context['RequestStatus']=models.RequestStatus
        return context
