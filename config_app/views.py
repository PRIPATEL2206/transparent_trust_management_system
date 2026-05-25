from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.contrib import messages

from roles.decorators import role_required
from .models import SiteConfig
from .forms import SiteConfigForm


@role_required('super_admin')
def site_config_view(request: HttpRequest):
    config = SiteConfig.get_instance()
    form = SiteConfigForm(instance=config)

    if request.method == 'POST':
        form = SiteConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Site configuration updated successfully.")
            return redirect('site_config')

    return render(request, 'config_app/site_config.html', {'form': form})
