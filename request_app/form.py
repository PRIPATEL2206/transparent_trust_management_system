
from django import forms
from .models import RequestMessage

class RequestMessageForm(forms.ModelForm):
    class Meta:
        model = RequestMessage
        fields = ["message"]

        widgets = {
            "message": forms.Textarea(attrs={
                "rows": 2,
                "class": "w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Write a message...",
            })
        }

        labels = {
            "message": "Message",
        }
