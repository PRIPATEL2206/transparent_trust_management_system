from django.shortcuts import render,redirect
from django.views.generic import DetailView,CreateView
from django.db.models import Q

from . import models,forms

# Create your views here.
# cckdmkcmd

class RequestDetailView(DetailView):
    model = models.Request
    template_name = "request/detail.html"
    context_object_name = "Request"
    context_object_name = "request_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_obj = self.get_object()
        context['can_approve'] =  request_obj.can_approve(self.request.user)
        context['can_cancel'] = request_obj.can_cancel(self.request.user)
        context['can_chat'] = request_obj.can_chat(self.request.user)
        context['messages'] = request_obj.messages.all()
        context['form'] = forms.RequestMessageForm(self.request.POST)
        return context

class RequestMessageCreateView(CreateView):
    model = models.RequestMessage
    form_class = forms.RequestMessageForm

    def post(self,request,pk,*args,**kwargs):  
        requestMassge=models.RequestMessage.objects.create(sender=request.user,request=models.Request.objects.get(pk=pk),massges=request.POST.get('massges'))
        return redirect('request_app:detail',pk=pk)

