from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404

from roles.decorators import admin_required
from services.rate_limit import rate_limit
from services.csv_utils import make_file_response
from .models import GeneratedReport
from .forms import ReportGenerateForm
from .services import ReportService


@admin_required
@rate_limit(max_attempts=5, window=300, key_prefix='report_gen')
def report_generate_view(request: HttpRequest):
    form = ReportGenerateForm()
    reports = GeneratedReport.objects.filter(generated_by=request.user).order_by('-created_at')[:20]

    if request.method == 'POST':
        form = ReportGenerateForm(request.POST)
        if form.is_valid():
            report = ReportService.generate_report(
                report_type=form.cleaned_data['report_type'],
                date_from=form.cleaned_data['date_from'],
                date_to=form.cleaned_data['date_to'],
                format=form.cleaned_data['format'],
                generated_by=request.user,
            )
            return report_download_view(request, report.id)

    context = {'form': form, 'reports': reports}
    return render(request, 'reports/report_generate.html', context)


@admin_required
def report_download_view(request: HttpRequest, report_id: int):
    report = get_object_or_404(GeneratedReport, id=report_id, generated_by=request.user)
    content_type = 'text/csv' if report.format == 'csv' else 'application/pdf'
    with report.file.open('rb') as f:
        content = f.read()
    filename = report.file.name.split("/")[-1]
    return make_file_response(content, filename, content_type)
