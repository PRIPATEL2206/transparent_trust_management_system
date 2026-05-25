import logging
import time

from django.contrib.auth.decorators import login_not_required
from django.core.cache import cache
from django.http import HttpResponse

logger = logging.getLogger('services')


@login_not_required
def admin_honeypot_view(request, path=''):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '0.0.0.0')
    ua = request.META.get('HTTP_USER_AGENT', '')[:200]

    logger.warning(
        'Admin honeypot triggered: %s %s | ip=%s ua=%s [%s]',
        request.method, request.get_full_path(),
        ip, ua, getattr(request, 'request_id', '-')
    )

    probe_key = f'honeypot_probe:{ip}'
    count = cache.get(probe_key, 0) + 1
    cache.set(probe_key, count, 3600)

    if count >= 3:
        logger.warning('Repeated honeypot probes from ip=%s (count=%d)', ip, count)

    time.sleep(2)
    return HttpResponse(
        '<html><head><title>Log in | Django site admin</title></head>'
        '<body><h1>Server Error (500)</h1></body></html>',
        status=503,
        content_type='text/html',
    )
