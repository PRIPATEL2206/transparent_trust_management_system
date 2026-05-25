from django import forms
from django.contrib.auth.models import User
from .models import ChatGroup


class ChatGroupForm(forms.ModelForm):
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500', 'rows': 3}),
    )

    class Meta:
        model = ChatGroup
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'}),
        }


class AddMemberForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500',
            'placeholder': 'Enter username'
        })
    )
