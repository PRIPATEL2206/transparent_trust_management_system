from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from a_customeauth.models import Profile

INPUT_CLASS = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500'


class RegisterForm(forms.Form):
    username = forms.CharField(
        min_length=3, max_length=30,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Password'})
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Confirm password'})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned_data


class ProfileUpdateForm(forms.Form):
    avatar = forms.ImageField(
        show_hidden_initial=True,
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100'
        })
    )
    username = forms.CharField(
        min_length=3, max_length=30,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS})
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS})
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS})
    )

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username__iexact=username)
        if self.current_user:
            qs = qs.exclude(pk=self.current_user.pk)
        if qs.exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email__iexact=email)
        if self.current_user:
            qs = qs.exclude(pk=self.current_user.pk)
        if qs.exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and hasattr(avatar, 'content_type'):
            from services.file_validators import validate_upload_image
            validate_upload_image(avatar)
        return avatar

