import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client


@pytest.mark.django_db
class TestRegisterView:

    def setup_method(self):
        self.client = Client()
        cache.clear()

    def test_register_page_renders(self):
        response = self.client.get('/auth/register/')
        assert response.status_code == 200

    def test_register_success(self):
        response = self.client.post('/auth/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass99!@',
            'password_confirm': 'StrongPass99!@',
        })
        assert response.status_code == 302
        assert response.url == '/'
        assert User.objects.filter(username='newuser').exists()

    def test_register_creates_profile(self):
        self.client.post('/auth/register/', {
            'username': 'profileuser',
            'email': 'profile@example.com',
            'password': 'StrongPass99!@',
            'password_confirm': 'StrongPass99!@',
        })
        user = User.objects.get(username='profileuser')
        assert hasattr(user, 'profile')

    def test_register_creates_role(self):
        self.client.post('/auth/register/', {
            'username': 'roleuser',
            'email': 'role@example.com',
            'password': 'StrongPass99!@',
            'password_confirm': 'StrongPass99!@',
        })
        user = User.objects.get(username='roleuser')
        from roles.models import UserRole
        assert UserRole.objects.filter(user=user, role='user').exists()

    def test_register_logs_in_user(self):
        self.client.post('/auth/register/', {
            'username': 'autologin',
            'email': 'auto@example.com',
            'password': 'StrongPass99!@',
            'password_confirm': 'StrongPass99!@',
        })
        response = self.client.get('/auth/profile/')
        assert response.status_code == 200

    def test_register_duplicate_username(self):
        User.objects.create_user(username='taken', password='x', email='a@b.com')
        response = self.client.post('/auth/register/', {
            'username': 'taken',
            'email': 'other@example.com',
            'password': 'StrongPass99!@',
            'password_confirm': 'StrongPass99!@',
        })
        assert response.status_code == 200
        assert b'already taken' in response.content

    def test_register_duplicate_email(self):
        User.objects.create_user(username='first', password='x', email='dupe@example.com')
        response = self.client.post('/auth/register/', {
            'username': 'second',
            'email': 'dupe@example.com',
            'password': 'StrongPass99!@',
            'password_confirm': 'StrongPass99!@',
        })
        assert response.status_code == 200
        assert b'already exists' in response.content

    def test_register_password_mismatch(self):
        response = self.client.post('/auth/register/', {
            'username': 'mismatch',
            'email': 'mis@example.com',
            'password': 'StrongPass99!@',
            'password_confirm': 'DifferentPass!@',
        })
        assert response.status_code == 200
        assert b'do not match' in response.content

    def test_register_weak_password(self):
        response = self.client.post('/auth/register/', {
            'username': 'weakpwd',
            'email': 'weak@example.com',
            'password': '123',
            'password_confirm': '123',
        })
        assert response.status_code == 200
        assert User.objects.filter(username='weakpwd').count() == 0

    def test_register_short_username(self):
        response = self.client.post('/auth/register/', {
            'username': 'ab',
            'email': 'short@example.com',
            'password': 'StrongPass99!@',
            'password_confirm': 'StrongPass99!@',
        })
        assert response.status_code == 200
        assert User.objects.filter(username='ab').count() == 0

    def test_register_rate_limited(self):
        for i in range(3):
            self.client.post('/auth/register/', {
                'username': f'ratelimit{i}',
                'email': f'rate{i}@example.com',
                'password': 'bad',
                'password_confirm': 'bad',
            })

        response = self.client.post('/auth/register/', {
            'username': 'ratelimit3',
            'email': 'rate3@example.com',
            'password': 'StrongPass99!@',
            'password_confirm': 'StrongPass99!@',
        })
        assert response.status_code == 429
