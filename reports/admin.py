from django.contrib import admin
from .models import GeneratedReport


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'format', 'date_from', 'date_to', 'generated_by', 'created_at')
    list_filter = ('report_type', 'format', 'created_at')
    date_hierarchy = 'created_at'
