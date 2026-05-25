import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client


@pytest.mark.django_db
class TestLoginView:

    def setup_method(self):
        self.client = Client()
        self.password = 'SecurePass123!@#'
        self.user = User.objects.create_user(
            username='logintest', email='login@test.com', password=self.password
        )
        cache.clear()

    def test_login_page_renders(self):
        response = self.client.get('/auth/login/')
        assert response.status_code == 200

    def test_login_success(self):
        response = self.client.post('/auth/login/', {
            'username': 'logintest',
            'password': self.password,
        })
        assert response.status_code == 302
        assert response.url == '/'

    def test_login_success_redirect_next(self):
        response = self.client.post('/auth/login/?next=/expenses/', {
            'username': 'logintest',
            'password': self.password,
        })
        assert response.status_code == 302
        assert response.url == '/expenses/'

    def test_login_rejects_unsafe_next(self):
        response = self.client.post('/auth/login/?next=http://evil.com/', {
            'username': 'logintest',
            'password': self.password,
        })
        assert response.status_code == 302
        assert response.url == '/'

    def test_login_wrong_password(self):
        response = self.client.post('/auth/login/', {
            'username': 'logintest',
            'password': 'wrongpassword',
        })
        assert response.status_code == 200
        assert b'Invalid username or password' in response.content

    def test_login_nonexistent_user(self):
        response = self.client.post('/auth/login/', {
            'username': 'nonexistent',
            'password': 'anypass',
        })
        assert response.status_code == 200
        assert b'Invalid username or password' in response.content

    def test_login_empty_fields(self):
        response = self.client.post('/auth/login/', {
            'username': '',
            'password': '',
        })
        assert response.status_code == 200
        assert b'Please enter both username and password' in response.content

    def test_login_account_lockout_after_5_failures(self):
        for _ in range(5):
            self.client.post('/auth/login/', {
                'username': 'logintest',
                'password': 'wrong',
            })

        response = self.client.post('/auth/login/', {
            'username': 'logintest',
            'password': self.password,
        })
        assert response.status_code == 200
        assert b'temporarily locked' in response.content

    def test_login_lockout_is_per_account(self):
        other_user = User.objects.create_user(
            username='otheruser', password='OtherPass123!@#'
        )
        for _ in range(5):
            self.client.post('/auth/login/', {
                'username': 'logintest',
                'password': 'wrong',
            })

        response = self.client.post('/auth/login/', {
            'username': 'otheruser',
            'password': 'OtherPass123!@#',
        })
        assert response.status_code == 302

    def test_login_deactivated_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post('/auth/login/', {
            'username': 'logintest',
            'password': self.password,
        })
        assert response.status_code == 200
        assert b'deactivated' in response.content

    def test_login_sets_session(self):
        self.client.post('/auth/login/', {
            'username': 'logintest',
            'password': self.password,
        })
        response = self.client.get('/auth/profile/')
        assert response.status_code == 200

    def test_login_records_history(self):
        from a_customeauth.models import LoginHistory
        self.client.post('/auth/login/', {
            'username': 'logintest',
            'password': self.password,
        })
        assert LoginHistory.objects.filter(user=self.user, success=True).exists()

    def test_login_failed_records_history(self):
        from a_customeauth.models import LoginHistory
        self.client.post('/auth/login/', {
            'username': 'logintest',
            'password': 'wrong',
        })
        assert LoginHistory.objects.filter(user=self.user, success=False).exists()


@pytest.mark.django_db
class TestLogoutView:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='logouttest', password='SecurePass123!@#'
        )
        self.client.login(username='logouttest', password='SecurePass123!@#')

    def test_logout_requires_post(self):
        response = self.client.get('/auth/logout/')
        assert response.status_code == 405

    def test_logout_success(self):
        response = self.client.post('/auth/logout/')
        assert response.status_code == 302
        assert response.url == '/auth/login/'

    def test_logout_clears_session(self):
        self.client.post('/auth/logout/')
        response = self.client.get('/auth/profile/')
        assert response.status_code == 302
        assert '/auth/login' in response.url
