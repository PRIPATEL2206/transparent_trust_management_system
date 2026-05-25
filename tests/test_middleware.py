import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, override_settings


@pytest.mark.django_db
class TestGlobalThrottleMiddleware:

    def setup_method(self):
        self.client = Client()
        cache.clear()

    @override_settings(THROTTLE_MAX_REQUESTS=3, THROTTLE_WINDOW=60)
    def test_allows_requests_under_limit(self):
        for _ in range(3):
            response = self.client.get('/')
            assert response.status_code == 200

    @override_settings(THROTTLE_MAX_REQUESTS=3, THROTTLE_WINDOW=60)
    def test_blocks_after_limit_exceeded(self):
        for _ in range(3):
            self.client.get('/')

        response = self.client.get('/')
        assert response.status_code == 429

    @override_settings(THROTTLE_MAX_REQUESTS=3, THROTTLE_WINDOW=60)
    def test_health_endpoint_exempt(self):
        for _ in range(5):
            response = self.client.get('/health/')
            assert response.status_code == 200

    def test_rate_limit_headers_present(self):
        response = self.client.get('/')
        assert 'X-RateLimit-Limit' in response
        assert 'X-RateLimit-Remaining' in response


@pytest.mark.django_db
class TestSecurityHeadersMiddleware:

    def setup_method(self):
        self.client = Client()
        cache.clear()

    def test_csp_header_present(self):
        response = self.client.get('/')
        assert 'Content-Security-Policy' in response

    def test_csp_contains_nonce(self):
        response = self.client.get('/')
        csp = response['Content-Security-Policy']
        assert 'nonce-' in csp

    def test_referrer_policy_present(self):
        response = self.client.get('/')
        assert response['Referrer-Policy'] == 'strict-origin-when-cross-origin'

    def test_permissions_policy_present(self):
        response = self.client.get('/')
        assert 'camera=()' in response['Permissions-Policy']

    def test_x_content_type_options_present(self):
        response = self.client.get('/')
        assert response['X-Content-Type-Options'] == 'nosniff'

    def test_cross_origin_opener_policy(self):
        response = self.client.get('/')
        assert response['Cross-Origin-Opener-Policy'] == 'same-origin'


@pytest.mark.django_db
class TestRequestIDMiddleware:

    def setup_method(self):
        self.client = Client()

    def test_response_has_request_id(self):
        response = self.client.get('/')
        assert 'X-Request-ID' in response

    def test_custom_request_id_honored(self):
        response = self.client.get('/', HTTP_X_REQUEST_ID='custom-123')
        assert response['X-Request-ID'] == 'custom-123'


@pytest.mark.django_db
class TestRequestTimingMiddleware:

    def setup_method(self):
        self.client = Client()

    def test_duration_header_present(self):
        response = self.client.get('/')
        assert 'X-Request-Duration-Ms' in response

    def test_duration_is_numeric(self):
        response = self.client.get('/')
        duration = response['X-Request-Duration-Ms']
        assert float(duration) >= 0


@pytest.mark.django_db
class TestAdminHoneypot:

    def setup_method(self):
        self.client = Client()
        cache.clear()

    def test_admin_path_returns_503(self):
        response = self.client.get('/admin/')
        assert response.status_code == 503

    def test_admin_login_path_returns_503(self):
        response = self.client.get('/admin/login/')
        assert response.status_code == 503

    def test_admin_subpath_trapped(self):
        response = self.client.get('/admin/auth/user/')
        assert response.status_code == 503


@pytest.mark.django_db
class TestRequestBodySizeMiddleware:

    def setup_method(self):
        self.client = Client()

    def test_normal_request_passes(self):
        response = self.client.post('/auth/login/', {
            'username': 'x', 'password': 'y'
        })
        assert response.status_code != 413

    def test_oversized_content_length_rejected(self):
        response = self.client.get('/', CONTENT_LENGTH='999999999')
        assert response.status_code == 413


@pytest.mark.django_db
class TestLivenessReadinessProbes:

    def setup_method(self):
        self.client = Client()

    def test_liveness_returns_alive(self):
        response = self.client.get('/health/live/')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'alive'

    def test_readiness_returns_ready(self):
        response = self.client.get('/health/ready/')
        assert response.status_code == 200
        data = response.json()
        assert data['ready'] is True
        assert data['checks']['database'] is True
