from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def email_verification_required(fun):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_email_verified:
            return redirect('verify_email_send')
        return fun(request, *args, **kwargs)
    return login_required(wrapper)