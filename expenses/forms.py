from django import forms
from .models import Expense, ExpenseCategory
from services.sanitize import sanitize_text

ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.pdf')
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class ExpenseForm(forms.ModelForm):
    description = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500', 'rows': 4}),
    )

    class Meta:
        model = Expense
        fields = ['title', 'description', 'amount', 'category', 'receipt']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500', 'min': '0.01', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'}),
            'receipt': forms.FileInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md', 'accept': '.jpg,.jpeg,.png,.gif,.pdf'}),
        }

    def clean_description(self):
        return sanitize_text(self.cleaned_data.get('description', ''))

    def clean_receipt(self):
        receipt = self.cleaned_data.get('receipt')
        if receipt:
            if receipt.content_type not in ALLOWED_FILE_TYPES:
                raise forms.ValidationError('Only JPEG, PNG, GIF, and PDF files are allowed.')
            if not receipt.name.lower().endswith(ALLOWED_EXTENSIONS):
                raise forms.ValidationError('Only JPEG, PNG, GIF, and PDF files are allowed.')
            if receipt.size > MAX_FILE_SIZE:
                raise forms.ValidationError('File size must be under 5MB.')
            from services.file_validators import validate_upload_document
            validate_upload_document(receipt)
        return receipt
