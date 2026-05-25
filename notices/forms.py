from django import forms
from .models import Notice
from services.sanitize import sanitize_text


class NoticeForm(forms.ModelForm):
    content = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500', 'rows': 5}),
    )

    class Meta:
        model = Notice
        fields = ['title', 'content', 'priority', 'expires_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'}),
            'priority': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500', 'type': 'datetime-local'}),
        }

    def clean_content(self):
        return sanitize_text(self.cleaned_data.get('content', ''))
