import pytest
import time
from unittest.mock import patch
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.test import Client, override_settings
from django.utils import timezone


@pytest.mark.django_db
class TestSessionIdleTimeout:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='sessionuser', password='SecurePass123!@#'
        )
        self.client.login(username='sessionuser', password='SecurePass123!@#')
        cache.clear()

    @override_settings(SESSION_IDLE_TIMEOUT=2)
    def test_idle_timeout_logs_out_user(self):
        session = self.client.session
        session['_last_activity'] = time.time() - 10
        session.save()

        response = self.client.get('/auth/profile/')
        assert response.status_code == 302
        assert '/auth/login' in response.url

    def test_active_session_stays_alive(self):
        response = self.client.get('/auth/profile/')
        assert response.status_code == 200

    @override_settings(SESSION_MAX_AGE=2)
    def test_hard_session_lifetime_enforced(self):
        session = self.client.session
        session['_session_start'] = time.time() - 10
        session.save()

        response = self.client.get('/auth/profile/')
        assert response.status_code == 302
        assert '/auth/login' in response.url


@pytest.mark.django_db
class TestMaxConcurrentSessions:

    def setup_method(self):
        cache.clear()

    @override_settings(MAX_SESSIONS_PER_USER=2)
    def test_max_sessions_evicts_oldest(self):
        user = User.objects.create_user(
            username='multisession', password='SecurePass123!@#'
        )

        client1 = Client()
        client1.login(username='multisession', password='SecurePass123!@#')
        session_key_1 = client1.session.session_key

        client2 = Client()
        client2.login(username='multisession', password='SecurePass123!@#')

        client3 = Client()
        client3.login(username='multisession', password='SecurePass123!@#')

        assert not Session.objects.filter(session_key=session_key_1).exists()


@pytest.mark.django_db
class TestSessionFingerprinting:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='fpuser', password='SecurePass123!@#'
        )
        cache.clear()

    def test_session_binds_user_agent(self):
        self.client.login(username='fpuser', password='SecurePass123!@#')

        response = self.client.get('/auth/profile/', HTTP_USER_AGENT='Mozilla/5.0 Chrome')
        assert response.status_code == 200

    def test_changed_user_agent_invalidates_session(self):
        self.client.defaults['HTTP_USER_AGENT'] = 'Mozilla/5.0 Chrome'
        self.client.login(username='fpuser', password='SecurePass123!@#')

        session = self.client.session
        session['_ua_fingerprint'] = 'original_hash_value'
        session.save()

        response = self.client.get('/auth/profile/', HTTP_USER_AGENT='curl/7.68')
        assert response.status_code == 302
        assert '/auth/login' in response.url
