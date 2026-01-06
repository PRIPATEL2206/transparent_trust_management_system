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
        print(request_data)
        print(confirm_password,password,accepted2,accepted1)
        if password != confirm_password :
            print("Passwords do not match")
            messages.error(request, "Passwords do not match")
            return redirect('register')
        if accepted1 != "on":
            print("Please accept the terms and conditions")
            messages.error(request, "Please accept the terms and conditions")
            return redirect('register')
        if accepted2 != "on":
            print("Please accept the privacy policy")
            messages.error(request, "Please accept the privacy policy")
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            print("Email already exists")
            messages.error(request, "Email already exists")
            return redirect('register')
        
        user = User.objects.create_user(**request_data)
        user.save()
        print("User created successfully")
        messages.success(request, "Account created successfully")
        return redirect('login')
            



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
