from django.contrib import admin
from .models import SchemeCategory,SchemeImages,RequestMessage,Request,Scheme,Donation

# Register your models here.
admin.site.register(SchemeCategory)
admin.site.register(SchemeImages)
admin.site.register(RequestMessage)
admin.site.register(Request)
admin.site.register(Scheme)
admin.site.register(Donation)