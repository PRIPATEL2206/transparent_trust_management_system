from django import forms


class PaymentForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500',
            'placeholder': 'Enter amount',
            'step': '0.01'
        })
    )
    transaction_type = forms.ChoiceField(
        choices=[('donation', 'Donation'), ('membership', 'Membership Fee'), ('fee', 'General Fee')],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500',
            'rows': 3,
            'placeholder': 'Optional notes'
        })
    )
