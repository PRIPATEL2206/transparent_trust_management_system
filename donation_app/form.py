# forms.py
from decimal import Decimal
from django import forms
from .models import Donation, Campaign,Currency,Visibility
from campaign.models import CampaignCategory
from django.utils import timezone
from django.contrib.auth import get_user_model


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

User = get_user_model()

BASE_INPUT_CLS = "w-full rounded-lg border-gray-300 focus:border-teal-600 focus:ring-2 focus:ring-teal-300"
SELECT_CLS = BASE_INPUT_CLS
TEXT_CLS = BASE_INPUT_CLS
NUMBER_CLS = BASE_INPUT_CLS
DATE_CLS = BASE_INPUT_CLS

class DonationFilterForm(forms.Form):
    campaign = forms.ModelChoiceField(
        queryset=Campaign.objects.all().order_by('title'),
        required=False, label="Campaign",
        widget=forms.Select(attrs={"class": SELECT_CLS})
    )
    category = forms.ModelChoiceField(
        queryset=CampaignCategory.objects.all().order_by('id'),
        required=False, label="Category",
        widget=forms.Select(attrs={"class": SELECT_CLS})
    )
    donor = forms.ModelChoiceField(
        queryset=User.objects.all().order_by('id'),
        required=False, label="Donor",
        widget=forms.Select(attrs={"class": SELECT_CLS})
    )
    currency = forms.ChoiceField(
        choices=[('', 'Any')] + list(Currency.choices),
        required=False, label="Currency",
        widget=forms.Select(attrs={"class": SELECT_CLS})
    )
    visibility = forms.ChoiceField(
        choices=[('', 'Any')] + list(Visibility.choices),
        required=False, label="Visibility",
        widget=forms.Select(attrs={"class": SELECT_CLS})
    )

    amount_min = forms.DecimalField(required=False, min_value=0, label="Min Amount",
                                    widget=forms.NumberInput(attrs={"class": NUMBER_CLS, "placeholder": "0.00"}))
    amount_max = forms.DecimalField(required=False, min_value=0, label="Max Amount",
                                    widget=forms.NumberInput(attrs={"class": NUMBER_CLS, "placeholder": "99999.99"}))

    created_from = forms.DateField(
        required=False, input_formats=['%Y-%m-%d'], label="Created From",
        widget=forms.DateInput(attrs={"type": "date", "class": DATE_CLS})
    )
    created_to = forms.DateField(
        required=False, input_formats=['%Y-%m-%d'], label="Created To",
        widget=forms.DateInput(attrs={"type": "date", "class": DATE_CLS})
    )

    has_payment = forms.ChoiceField(
        choices=[('', 'Any'), ('1', 'Yes'), ('0', 'No')],
        required=False, label="Has Payment",
        widget=forms.Select(attrs={"class": SELECT_CLS})
    )

    q = forms.CharField(required=False, label="Search",
                        widget=forms.TextInput(attrs={"class": TEXT_CLS, "placeholder": "title/desc/name"}))

    tags = forms.CharField(required=False, label="Tag(s)",
                           widget=forms.TextInput(attrs={"class": TEXT_CLS, "placeholder": "e.g. education, health"}))

    ordering = forms.ChoiceField(
        required=False, label="Order By",
        choices=[
            ('-created', 'Newest'),
            ('created', 'Oldest'),
            ('-amount', 'Amount (high → low)'),
            ('amount', 'Amount (low → high)'),
        ],
        widget=forms.Select(attrs={"class": SELECT_CLS})
    )

    def clean(self):
        cleaned = super().clean()
        min_amt = cleaned.get('amount_min')
        max_amt = cleaned.get('amount_max')
        if min_amt is not None and max_amt is not None and min_amt > max_amt:
            self.add_error('amount_max', 'Max amount must be ≥ min amount.')

        start = cleaned.get('created_from')
        end = cleaned.get('created_to')
        if start and end and start > end:
            self.add_error('created_to', 'End date must be ≥ start date.')
        return cleaned