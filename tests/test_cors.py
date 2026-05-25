import pytest
from django.test import Client, RequestFactory, override_settings
from django.http import HttpResponse
from django.core.cache import cache

from services.cors import CORSMiddleware


def dummy_view(request):
    return HttpResponse('OK', status=200)


class TestCORSMiddleware:

    def setup_method(self):
        self.factory = RequestFactory()

    def _get_middleware(self, allowed_origins=None, credentials=False):
        with self.settings(
            CORS_ALLOWED_ORIGINS=allowed_origins or [],
            CORS_ALLOW_CREDENTIALS=credentials,
            CORS_MAX_AGE=3600,
            API_PREFIX='/api/'
        ):
            return CORSMiddleware(dummy_view)

    def settings(self, **kwargs):
        return override_settings(**kwargs)

    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://example.com'],
        CORS_ALLOW_CREDENTIALS=False,
        CORS_MAX_AGE=3600,
        API_PREFIX='/api/'
    )
    def test_non_api_path_no_cors_headers(self):
        middleware = CORSMiddleware(dummy_view)
        request = self.factory.get('/', HTTP_ORIGIN='https://example.com')
        response = middleware(request)
        assert 'Access-Control-Allow-Origin' not in response

    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://example.com'],
        CORS_ALLOW_CREDENTIALS=False,
        CORS_MAX_AGE=3600,
        API_PREFIX='/api/'
    )
    def test_api_path_with_allowed_origin(self):
        middleware = CORSMiddleware(dummy_view)
        request = self.factory.get('/api/data/', HTTP_ORIGIN='https://example.com')
        response = middleware(request)
        assert response['Access-Control-Allow-Origin'] == 'https://example.com'
        assert 'Vary' in response

    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://example.com'],
        CORS_ALLOW_CREDENTIALS=False,
        CORS_MAX_AGE=3600,
        API_PREFIX='/api/'
    )
    def test_api_path_with_disallowed_origin(self):
        middleware = CORSMiddleware(dummy_view)
        request = self.factory.get('/api/data/', HTTP_ORIGIN='https://evil.com')
        response = middleware(request)
        assert 'Access-Control-Allow-Origin' not in response

    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://example.com'],
        CORS_ALLOW_CREDENTIALS=False,
        CORS_MAX_AGE=3600,
        API_PREFIX='/api/'
    )
    def test_preflight_returns_204(self):
        middleware = CORSMiddleware(dummy_view)
        request = self.factory.options('/api/data/', HTTP_ORIGIN='https://example.com')
        response = middleware(request)
        assert response.status_code == 204
        assert response['Access-Control-Max-Age'] == '3600'

    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://example.com'],
        CORS_ALLOW_CREDENTIALS=False,
        CORS_MAX_AGE=3600,
        API_PREFIX='/api/'
    )
    def test_preflight_includes_allowed_methods(self):
        middleware = CORSMiddleware(dummy_view)
        request = self.factory.options('/api/data/', HTTP_ORIGIN='https://example.com')
        response = middleware(request)
        methods = response['Access-Control-Allow-Methods']
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'DELETE' in methods

    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://example.com'],
        CORS_ALLOW_CREDENTIALS=False,
        CORS_MAX_AGE=3600,
        API_PREFIX='/api/'
    )
    def test_preflight_includes_allowed_headers(self):
        middleware = CORSMiddleware(dummy_view)
        request = self.factory.options('/api/data/', HTTP_ORIGIN='https://example.com')
        response = middleware(request)
        headers = response['Access-Control-Allow-Headers']
        assert 'Content-Type' in headers
        assert 'Authorization' in headers
        assert 'X-CSRFToken' in headers

    @override_settings(
        CORS_ALLOWED_ORIGINS=['*'],
        CORS_ALLOW_CREDENTIALS=False,
        CORS_MAX_AGE=86400,
        API_PREFIX='/api/'
    )
    def test_wildcard_origin(self):
        middleware = CORSMiddleware(dummy_view)
        request = self.factory.get('/api/data/', HTTP_ORIGIN='https://anything.com')
        response = middleware(request)
        assert response['Access-Control-Allow-Origin'] == '*'

    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://example.com'],
        CORS_ALLOW_CREDENTIALS=True,
        CORS_MAX_AGE=86400,
        API_PREFIX='/api/'
    )
    def test_credentials_header_when_enabled(self):
        middleware = CORSMiddleware(dummy_view)
        request = self.factory.get('/api/data/', HTTP_ORIGIN='https://example.com')
        response = middleware(request)
        assert response['Access-Control-Allow-Credentials'] == 'true'

    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://example.com'],
        CORS_ALLOW_CREDENTIALS=False,
        CORS_MAX_AGE=86400,
        API_PREFIX='/api/'
    )
    def test_no_credentials_header_when_disabled(self):
        middleware = CORSMiddleware(dummy_view)
        request = self.factory.get('/api/data/', HTTP_ORIGIN='https://example.com')
        response = middleware(request)
        assert 'Access-Control-Allow-Credentials' not in response

    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://example.com'],
        CORS_ALLOW_CREDENTIALS=False,
        CORS_MAX_AGE=86400,
        API_PREFIX='/api/'
    )
    def test_no_origin_header_no_cors(self):
        middleware = CORSMiddleware(dummy_view)
        request = self.factory.get('/api/data/')
        response = middleware(request)
        assert 'Access-Control-Allow-Origin' not in response

    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://site-a.com', 'https://site-b.com'],
        CORS_ALLOW_CREDENTIALS=False,
        CORS_MAX_AGE=86400,
        API_PREFIX='/api/'
    )
    def test_multiple_allowed_origins(self):
        middleware = CORSMiddleware(dummy_view)
        req_a = self.factory.get('/api/data/', HTTP_ORIGIN='https://site-a.com')
        req_b = self.factory.get('/api/data/', HTTP_ORIGIN='https://site-b.com')
        assert middleware(req_a)['Access-Control-Allow-Origin'] == 'https://site-a.com'
        assert middleware(req_b)['Access-Control-Allow-Origin'] == 'https://site-b.com'
