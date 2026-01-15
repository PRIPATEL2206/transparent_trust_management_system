from django.shortcuts import render
from .form import SchemeForm
from django.views.generic import View
from .models import Scheme,SchemeImages
from django.shortcuts import render, redirect
from django.contrib import messages
from account.decorators import email_verification_required


# Create your views here.
@method_decorator(email_verification_required, name='dispatch')
class CreateCampaignView(View):
    template_name = "campaign/create_campaign.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        form = SchemeForm(request.POST, request.FILES)
        if form.is_valid():
            scheme = form.save(request.user)
            messages.success(request, "campais request sended successfully")

        return render(request, self.template_name, {"form": form})

