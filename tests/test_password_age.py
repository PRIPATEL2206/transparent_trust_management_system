import pytest
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, override_settings
from django.utils import timezone


@pytest.mark.django_db
class TestPasswordAgeMiddleware:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='ageuser', password='SecurePass123!@#', email='age@test.com'
        )
        cache.clear()

    @override_settings(PASSWORD_MAX_AGE_DAYS=90)
    def test_fresh_password_no_redirect(self):
        profile = self.user.profile
        profile.password_changed_at = timezone.now()
        profile.save()
        self.client.login(username='ageuser', password='SecurePass123!@#')
        response = self.client.get('/')
        assert response.status_code == 200

    @override_settings(PASSWORD_MAX_AGE_DAYS=90)
    def test_expired_password_redirects(self):
        profile = self.user.profile
        profile.password_changed_at = timezone.now() - timedelta(days=91)
        profile.save()
        self.client.login(username='ageuser', password='SecurePass123!@#')
        response = self.client.get('/')
        assert response.status_code == 302
        assert '/auth/settings' in response.url

    @override_settings(PASSWORD_MAX_AGE_DAYS=90)
    def test_settings_page_exempt_from_redirect(self):
        profile = self.user.profile
        profile.password_changed_at = timezone.now() - timedelta(days=100)
        profile.save()
        self.client.login(username='ageuser', password='SecurePass123!@#')
        response = self.client.get('/auth/settings/')
        assert response.status_code == 200

    @override_settings(PASSWORD_MAX_AGE_DAYS=90)
    def test_logout_exempt_from_redirect(self):
        profile = self.user.profile
        profile.password_changed_at = timezone.now() - timedelta(days=100)
        profile.save()
        self.client.login(username='ageuser', password='SecurePass123!@#')
        response = self.client.get('/auth/logout/')
        assert response.status_code != 302 or '/auth/settings' not in response.get('Location', '')

    @override_settings(PASSWORD_MAX_AGE_DAYS=90)
    def test_health_endpoint_exempt(self):
        profile = self.user.profile
        profile.password_changed_at = timezone.now() - timedelta(days=100)
        profile.save()
        self.client.login(username='ageuser', password='SecurePass123!@#')
        response = self.client.get('/health/')
        assert response.status_code == 200

    @override_settings(PASSWORD_MAX_AGE_DAYS=0)
    def test_disabled_when_max_age_zero(self):
        profile = self.user.profile
        profile.password_changed_at = timezone.now() - timedelta(days=500)
        profile.save()
        self.client.login(username='ageuser', password='SecurePass123!@#')
        response = self.client.get('/')
        assert response.status_code == 200

    @override_settings(PASSWORD_MAX_AGE_DAYS=90)
    def test_unauthenticated_user_not_affected(self):
        response = self.client.get('/')
        assert response.status_code == 200

    @override_settings(PASSWORD_MAX_AGE_DAYS=90)
    def test_fallback_to_date_joined_if_no_password_changed_at(self):
        profile = self.user.profile
        profile.password_changed_at = None
        profile.save()
        self.user.date_joined = timezone.now() - timedelta(days=100)
        self.user.save()
        self.client.login(username='ageuser', password='SecurePass123!@#')
        response = self.client.get('/')
        assert response.status_code == 302
        assert '/auth/settings' in response.url

    @override_settings(PASSWORD_MAX_AGE_DAYS=90)
    def test_recently_joined_no_password_changed_at_ok(self):
        profile = self.user.profile
        profile.password_changed_at = None
        profile.save()
        self.user.date_joined = timezone.now() - timedelta(days=5)
        self.user.save()
        self.client.login(username='ageuser', password='SecurePass123!@#')
        response = self.client.get('/')
        assert response.status_code == 200

    @override_settings(PASSWORD_MAX_AGE_DAYS=30)
    def test_shorter_max_age_triggers_sooner(self):
        profile = self.user.profile
        profile.password_changed_at = timezone.now() - timedelta(days=31)
        profile.save()
        self.client.login(username='ageuser', password='SecurePass123!@#')
        response = self.client.get('/')
        assert response.status_code == 302
        assert '/auth/settings' in response.url

    @override_settings(PASSWORD_MAX_AGE_DAYS=90)
    def test_static_path_exempt(self):
        profile = self.user.profile
        profile.password_changed_at = timezone.now() - timedelta(days=100)
        profile.save()
        self.client.login(username='ageuser', password='SecurePass123!@#')
        response = self.client.get('/static/js/script.js')
        assert response.status_code != 302 or '/auth/settings' not in response.get('Location', '')
