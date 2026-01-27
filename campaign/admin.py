from django.contrib import admin
from .models import CampaignCategory,CampaignImages,Campaign

# Register your models here.
admin.site.register(CampaignCategory)
admin.site.register(CampaignImages)
admin.site.register(Campaign)