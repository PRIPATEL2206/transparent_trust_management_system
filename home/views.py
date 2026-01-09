from django.shortcuts import render
from account.decorators import email_verification_required

@email_verification_required
def home(req):
    return render(req,"home/home.html")