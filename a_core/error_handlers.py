import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_not_required

logger = logging.getLogger('services')


@login_not_required
def custom_403(request, exception=None):
    return render(request, '403.html', status=403)


@login_not_required
def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


@login_not_required
def custom_500(request):
    user = getattr(request, 'user', None)
    username = user.username if user and hasattr(user, 'username') and user.is_authenticated else 'anonymous'
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '-')
    logger.error(
        'Unhandled 500: %s %s | user=%s ip=%s request_id=%s ua=%s',
        request.method, request.path,
        username, ip,
        getattr(request, 'request_id', '-'),
        request.META.get('HTTP_USER_AGENT', '-')[:100],
    )
    return render(request, '500.html', status=500)


@login_not_required
def csrf_failure(request, reason=''):
    logger.warning(
        'CSRF failure: %s %s | reason=%s ip=%s',
        request.method, request.path, reason,
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '-'),
    )
    return render(request, 'csrf_failure.html', {'reason': reason}, status=403)
