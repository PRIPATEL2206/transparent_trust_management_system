from django import forms
from .models import Donation, DonationType
from datetime import datetime
from services.sanitize import sanitize_text

INPUT_CLASS = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'


class AddDonationTypeForm(forms.ModelForm):
    desc = forms.CharField(
        max_length=2000,
        required=False,
        widget=forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
    )
    ending_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': INPUT_CLASS})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.visible_fields():
            if 'class' not in field.field.widget.attrs:
                field.field.widget.attrs['class'] = INPUT_CLASS

    def clean_desc(self):
        return sanitize_text(self.cleaned_data.get('desc', ''))

    class Meta:
        model = DonationType
        fields = ['name', 'desc', 'photo', 'is_forever', 'ending_date']


class AddDonationForm(forms.ModelForm):
    desc = forms.CharField(
        max_length=2000,
        required=False,
        widget=forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.visible_fields():
            if 'class' not in field.field.widget.attrs:
                field.field.widget.attrs['class'] = INPUT_CLASS

    def clean_desc(self):
        return sanitize_text(self.cleaned_data.get('desc', ''))

    class Meta:
        model = Donation
        fields = ['donation_for', 'amount', 'display_name', 'handover_by', 'desc']

        