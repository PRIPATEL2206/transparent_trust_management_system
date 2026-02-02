from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView,View
from django.shortcuts import render, redirect, resolve_url
from .models import CustomUser as User 
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.decorators import method_decorator

from .decorators import email_verification_required

# Create your views here.
class RegisterView(View):
    template_name = "account/register.html"
    def get(self, request):
        return render(request, self.template_name)
    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password1")
        confirm_password = request.POST.get("password2")
        accepted2 = request.POST.get("accepted2")
        accepted1 = request.POST.get("accepted1")

        request_data={
            'email' : request.POST.get("email"),
            'first_name' : request.POST.get("firstname"),
            'last_name' : request.POST.get("lastname"),
            'middel_name' : request.POST.get("middelname"),
            'stdcode' : request.POST.get("stdcode"),
            'phone' : request.POST.get("phone"),
            'address1' : request.POST.get("address1"),
            'address2' : request.POST.get("address2"),
            'city' : request.POST.get("city"),
            'state' : request.POST.get("state"),
            'country' : request.POST.get("country"),
            'zipcode' : request.POST.get("zipcode"),
            'password' : request.POST.get("password1"),
        }
        if password != confirm_password :
            messages.error(request, "Passwords do not match")
            return redirect('register')
        if accepted1 != "on":
            messages.error(request, "Please accept the terms and conditions")
            return redirect('register')
        if accepted2 != "on":
            messages.error(request, "Please accept the privacy policy")
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('register')
        
        user = User.objects.create_user(**request_data)
        user.save()
        _send_verification_email(request, user)

        return redirect('email_sent')

def _send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    verification_link = request.build_absolute_uri(
        reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    )

    send_mail(
        subject="Verify your email",
        message=f"Click the link to verify your email:\n{verification_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


class VerifyEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_email_verified = True
            user.is_active = True
            user.save()
            return redirect('email_verified')
        else:
            return redirect('email_verification_failed')

class ResendVerificationView(View):
    def post(self, request):
        email = request.POST.get("email")
        user = User.objects.filter(email=email, is_email_verified=False).first()

        if user:
            _send_verification_email(request, user)

        return redirect('email_sent')
            
class LoginView(View):
    template_name = "account/login.html"
    def get(self, request):
        return render(request, self.template_name)
    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if not user.is_email_verified:
                _send_verification_email(request, user)
                messages.error(request, "Please verify your email first.")
                return redirect('email_sent')
            login(request, user)
            messages.success(request, "Logged in successfully")
            return redirect('home')
        else:
            messages.error(request, "Invalid login credentials")
            print("Invalid login credentials", email, password)
            return redirect('login')

def logoutView(request):
    logout(request)
    return redirect('login')

@method_decorator(email_verification_required, name='dispatch')
class ProfileUpdateView(View):
    template_name = "account/edit_profile.html"
    
    def get(self, request):
        user = request.user
        context = {'user': user}
        return render(request, self.template_name, context)
    
    def post(self, request):
        user = request.user

        # Update user fields
        for field in ['first_name', 'middel_name', 'last_name', 'stdcode', 'phone', 
                      'address1', 'address2', 'city', 'state', 'country', 'zipcode']:
            if field in request.POST:
                setattr(user, field, request.POST.get(field))
        
        if 'remove_profile_image' in request.POST:
            user.profile_image.delete()
        elif 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
            
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
