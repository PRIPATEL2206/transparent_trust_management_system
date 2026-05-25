from django.core.cache import cache
from django.http import HttpResponse
from functools import wraps


def rate_limit(max_attempts=5, window=300, key_prefix='ratelimit'):
    """
    Rate limit decorator. Blocks requests after max_attempts within window seconds.
    Uses Django's cache framework (works with any cache backend).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method != 'POST':
                return view_func(request, *args, **kwargs)

            ip = _get_client_ip(request)
            cache_key = f'{key_prefix}:{ip}'

            attempts = cache.get(cache_key, 0)
            if attempts >= max_attempts:
                return HttpResponse(
                    '<h1>Too Many Requests</h1>'
                    '<p>You have made too many attempts. Please try again later.</p>',
                    status=429,
                    content_type='text/html'
                )

            response = view_func(request, *args, **kwargs)

            if response.status_code != 302:
                cache.set(cache_key, attempts + 1, window)

            return response
        return wrapper
    return decorator


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')
