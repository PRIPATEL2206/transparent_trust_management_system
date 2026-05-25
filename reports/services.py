import csv
import io
from datetime import date
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.template.loader import render_to_string

from services.base import BaseService, service_error_handler
from services.csv_utils import sanitize_csv_value
from services.exceptions import ValidationError
from .models import GeneratedReport


class ReportService(BaseService):

    @staticmethod
    @service_error_handler
    def generate_report(report_type: str, date_from: date, date_to: date,
                        format: str, generated_by: User) -> GeneratedReport:
        if date_from > date_to:
            raise ValidationError("Start date cannot be after end date")

        data = ReportService._get_report_data(report_type, date_from, date_to)

        if format == 'csv':
            content = ReportService._generate_csv(report_type, data)
            filename = f"{report_type}_{date_from}_{date_to}.csv"
        elif format == 'pdf':
            content = ReportService._generate_pdf(report_type, data, date_from, date_to)
            filename = f"{report_type}_{date_from}_{date_to}.pdf"
        else:
            raise ValidationError(f"Unsupported format: {format}")

        report = GeneratedReport(
            report_type=report_type,
            format=format,
            date_from=date_from,
            date_to=date_to,
            generated_by=generated_by,
        )
        report.file.save(filename, ContentFile(content), save=False)
        report.save()

        ReportService.log_action('report_generated', user=generated_by, report_type=report_type)
        return report

    @staticmethod
    def _get_report_data(report_type: str, date_from: date, date_to: date) -> list:
        if report_type == 'donations':
            from donations.models import Donation
            qs = Donation.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to
            ).select_related('add_by', 'donation_for')
            return [
                {
                    'Date': d.created_at.strftime('%Y-%m-%d'),
                    'Donor': d.display_name,
                    'Amount': str(d.amount),
                    'Type': d.donation_for.name if d.donation_for else '',
                    'Added By': d.add_by.username,
                }
                for d in qs
            ]

        elif report_type == 'expenses':
            from expenses.models import Expense
            qs = Expense.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to
            ).select_related('raised_by', 'category')
            return [
                {
                    'Date': e.created_at.strftime('%Y-%m-%d'),
                    'Title': e.title,
                    'Amount': str(e.amount),
                    'Category': e.category.name if e.category else '',
                    'Status': e.get_status_display(),
                    'Raised By': e.raised_by.username,
                }
                for e in qs
            ]

        elif report_type == 'transactions':
            from payments.models import Transaction
            qs = Transaction.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to
            ).select_related('user')
            return [
                {
                    'Date': t.created_at.strftime('%Y-%m-%d'),
                    'User': t.user.username,
                    'Type': t.get_transaction_type_display(),
                    'Amount': str(t.amount),
                    'Status': t.get_status_display(),
                }
                for t in qs
            ]

        elif report_type == 'members':
            qs = User.objects.filter(
                date_joined__date__gte=date_from,
                date_joined__date__lte=date_to
            )
            return [
                {
                    'Username': u.username,
                    'Email': u.email,
                    'Joined': u.date_joined.strftime('%Y-%m-%d'),
                    'Active': 'Yes' if u.is_active else 'No',
                }
                for u in qs
            ]

        return []

    @staticmethod
    def _generate_csv(report_type: str, data: list) -> bytes:
        if not data:
            return b"No data for the selected period"

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        for row in data:
            writer.writerow({k: sanitize_csv_value(v) for k, v in row.items()})
        return output.getvalue().encode('utf-8')

    @staticmethod
    def _generate_pdf(report_type: str, data: list, date_from: date, date_to: date) -> bytes:
        html_content = render_to_string('reports/report_pdf_template.html', {
            'report_type': report_type,
            'data': data,
            'date_from': date_from,
            'date_to': date_to,
            'headers': data[0].keys() if data else [],
        })
        try:
            from weasyprint import HTML
            return HTML(string=html_content).write_pdf()
        except ImportError:
            return html_content.encode('utf-8')
