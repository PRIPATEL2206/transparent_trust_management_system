from django.shortcuts import render
from django.views.generic import DetailView
from django.db.models import Q

from . import models

# Create your views here.

class RequestDetailView(DetailView):
    model = models.Request
    template_name = "request/detail.html"
    context_object_name = "Request"
    context_object_name = "request_obj"

    def get_queryset(self):
        if not self.request.user.is_approval_user:
            return super().get_queryset().filter(Q(proposed_by=self.request.user))
        return super().get_queryset()
    

