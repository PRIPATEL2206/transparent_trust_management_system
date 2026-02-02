# forms.py
from decimal import Decimal
from django import forms
from .models import Donation, Campaign,Currency

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['amount', 'currency', 'donor_display_name', 'description']
        widgets = {
            "currency" :  forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
            "amount": forms.NumberInput(attrs={
                "class": "w-full border rounded px-3 py-2",
                "min": "0.01",
                "step": "0.01",          # matches 2 decimal places
                "inputmode": "decimal",  # better mobile keyboard
                "placeholder": "Enter amount",}),
            'description': forms.TextInput(attrs={'placeholder': 'Optional message'}),
            'donor_display_name': forms.TextInput(attrs={'placeholder': 'Public name (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        self.campaign: Campaign = kwargs.pop('campaign', None)
        super().__init__(*args, **kwargs)
        # Keep the form concise
        self.fields['amount'].widget.attrs.update({'min': '0.01', 'step': '0.01'})
        # Optional: lock currency to the campaign currency if needed
        # self.fields['currency'].initial = self.campaign.default_currency if you have one

    def clean_amount(self):
        amount: Decimal = self.cleaned_data['amount']
        if amount <= Decimal('0'):
            raise forms.ValidationError("Amount must be greater than 0.")
        if self.campaign:
            min_amt = self.campaign.minimum_donation_amount or Decimal('0.00')
            max_amt = self.campaign.maximum_donation_amount  # can be None
            if amount < min_amt:
                raise forms.ValidationError(f"Minimum allowed is {min_amt}.")
            if max_amt is not None and amount > max_amt:
                raise forms.ValidationError(f"Maximum allowed is {max_amt}.")
        return amount