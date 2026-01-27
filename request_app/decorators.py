# from django.shortcuts import redirect

# def is_user_has_access_of_request(fun):
#     def wrapper(request, *args, **kwargs):
#         if not request.user.is_email_verified:
#             return redirect('verify_email_send')
#         return fun(request, *args, **kwargs)
#     return login_required(wrapper)