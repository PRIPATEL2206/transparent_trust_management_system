from django import forms
from .models import FundRequest

ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'application/pdf', 'application/msword',
                      'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class FundRequestForm(forms.ModelForm):
    description = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500', 'rows': 5}),
    )

    class Meta:
        model = FundRequest
        fields = ['title', 'description', 'amount_requested', 'supporting_documents']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'}),
            'amount_requested': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500', 'min': '0.01', 'step': '0.01'}),
            'supporting_documents': forms.FileInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md', 'accept': '.jpg,.jpeg,.png,.pdf,.doc,.docx'}),
        }

    def clean_supporting_documents(self):
        doc = self.cleaned_data.get('supporting_documents')
        if doc:
            if doc.content_type not in ALLOWED_FILE_TYPES:
                raise forms.ValidationError('Only JPEG, PNG, PDF, and Word documents are allowed.')
            if not doc.name.lower().endswith(ALLOWED_EXTENSIONS):
                raise forms.ValidationError('Only JPEG, PNG, PDF, and Word documents are allowed.')
            if doc.size > MAX_FILE_SIZE:
                raise forms.ValidationError('File size must be under 10MB.')
            from services.file_validators import validate_upload_document
            validate_upload_document(doc)
        return doc
