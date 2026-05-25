from django.conf import settings
from django.http import HttpResponse


class CORSMiddleware:
    """Lightweight CORS handler for API endpoints.

    Only applies to paths starting with API_PREFIX (default: /api/).
    Configured via settings:
        CORS_ALLOWED_ORIGINS = ['https://example.com']
        CORS_ALLOW_CREDENTIALS = True
        CORS_MAX_AGE = 86400
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.api_prefix = getattr(settings, 'API_PREFIX', '/api/')
        self.allowed_origins = set(getattr(settings, 'CORS_ALLOWED_ORIGINS', []))
        self.allow_credentials = getattr(settings, 'CORS_ALLOW_CREDENTIALS', False)
        self.max_age = str(getattr(settings, 'CORS_MAX_AGE', 86400))
        self.allowed_methods = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        self.allowed_headers = 'Content-Type, Authorization, X-Request-ID, X-CSRFToken'

    def __call__(self, request):
        if not request.path.startswith(self.api_prefix):
            return self.get_response(request)

        origin = request.META.get('HTTP_ORIGIN', '')

        if request.method == 'OPTIONS':
            response = HttpResponse(status=204)
            self._set_cors_headers(response, origin)
            response['Access-Control-Max-Age'] = self.max_age
            return response

        response = self.get_response(request)
        self._set_cors_headers(response, origin)
        return response

    def _set_cors_headers(self, response, origin):
        if not origin:
            return

        if '*' in self.allowed_origins:
            response['Access-Control-Allow-Origin'] = '*'
        elif origin in self.allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
            response['Vary'] = 'Origin'
        else:
            return

        response['Access-Control-Allow-Methods'] = self.allowed_methods
        response['Access-Control-Allow-Headers'] = self.allowed_headers

        if self.allow_credentials:
            response['Access-Control-Allow-Credentials'] = 'true'
