from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView,View
from django.shortcuts import render, redirect
from .models import CustomUser as User 

# Create your views here.
class RegisterView(View):
    template_name = "account/register.html"
    def get(self, request):
        return render(request, self.template_name)
    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password1")
        confirm_password = request.POST.get("password2")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        middel_name = request.POST.get("middel_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        print(email, password, confirm_password, first_name, last_name, middel_name, phone, address)
        if password == confirm_password:
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists")
                return redirect('register')
            else:
                user = User.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name, middel_name=middel_name, phone=phone, address=address)
                user.save()
                print("User created successfully")
                messages.success(request, "Account created successfully")
                return redirect('login')
        else:
            messages.error(request, "Passwords do not match")
            return redirect('register')



class LoginView(View):
    template_name = "account/login.html"
    def get(self, request):
        return render(request, self.template_name)
    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid login credentials")
            print("Invalid login credentials", email, password)
            return redirect('login')

def logoutView(request):
    logout(request)
    return redirect('login')
