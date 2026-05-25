from datetime import date, timedelta
from django import forms
from .models import GeneratedReport

INPUT_CLASS = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'


class ReportGenerateForm(forms.Form):
    report_type = forms.ChoiceField(
        choices=GeneratedReport.REPORT_TYPES,
        widget=forms.Select(attrs={'class': INPUT_CLASS})
    )
    format = forms.ChoiceField(
        choices=GeneratedReport.FORMAT_CHOICES,
        widget=forms.Select(attrs={'class': INPUT_CLASS})
    )
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'})
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'})
    )

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get('date_from')
        date_to = cleaned.get('date_to')

        if date_from and date_to:
            if date_from > date_to:
                raise forms.ValidationError("Start date cannot be after end date.")
            if (date_to - date_from).days > 365:
                raise forms.ValidationError("Date range cannot exceed 365 days.")
            if date_to > date.today():
                raise forms.ValidationError("End date cannot be in the future.")
        return cleaned
