from django import forms
from .models import SiteConfig

INPUT_CLASS = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'


class SiteConfigForm(forms.ModelForm):
    class Meta:
        model = SiteConfig
        fields = [
            'trust_name', 'trust_description',
            'membership_fee', 'user_join_fee', 'min_donation_amount',
            'meta_title', 'meta_description', 'meta_keywords',
            'contact_email', 'contact_phone', 'address',
        ]
        widgets = {
            'trust_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'trust_description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
            'membership_fee': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'user_join_fee': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'min_donation_amount': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'meta_title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'meta_description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 2}),
            'meta_keywords': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'comma-separated keywords'}),
            'contact_email': forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'contact_phone': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'address': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 2}),
        }
