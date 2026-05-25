import pytest
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import Client, override_settings
from django.utils import timezone


@pytest.mark.django_db
class TestPasswordChange:

    def setup_method(self):
        self.client = Client()
        self.old_password = 'OldSecure123!@#'
        self.new_password = 'NewSecure456!@#'
        self.user = User.objects.create_user(
            username='pwdchange', password=self.old_password, email='pwd@test.com'
        )
        self.client.login(username='pwdchange', password=self.old_password)
        cache.clear()

    def test_password_change_success(self):
        response = self.client.post('/auth/settings/', {
            'change_password': '1',
            'old_password': self.old_password,
            'new_password1': self.new_password,
            'new_password2': self.new_password,
        })
        assert response.status_code == 302

        self.client.logout()
        assert self.client.login(username='pwdchange', password=self.new_password)

    def test_password_change_wrong_old_password(self):
        response = self.client.post('/auth/settings/', {
            'change_password': '1',
            'old_password': 'wrongold',
            'new_password1': self.new_password,
            'new_password2': self.new_password,
        })
        assert response.status_code == 200
        assert self.client.login(username='pwdchange', password=self.old_password)

    def test_password_change_mismatch(self):
        response = self.client.post('/auth/settings/', {
            'change_password': '1',
            'old_password': self.old_password,
            'new_password1': self.new_password,
            'new_password2': 'Different456!@#',
        })
        assert response.status_code == 200

    def test_password_change_updates_timestamp(self):
        self.client.post('/auth/settings/', {
            'change_password': '1',
            'old_password': self.old_password,
            'new_password1': self.new_password,
            'new_password2': self.new_password,
        })
        self.user.refresh_from_db()
        assert self.user.profile.password_changed_at is not None

    def test_password_change_invalidates_other_sessions(self):
        other_client = Client()
        other_client.login(username='pwdchange', password=self.old_password)

        self.client.post('/auth/settings/', {
            'change_password': '1',
            'old_password': self.old_password,
            'new_password1': self.new_password,
            'new_password2': self.new_password,
        })

        response = other_client.get('/auth/profile/')
        assert response.status_code == 302
        assert '/auth/login' in response.url


@pytest.mark.django_db
class TestPasswordAgePolicy:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='ageuser', password='SecurePass123!@#', email='age@test.com'
        )
        self.client.login(username='ageuser', password='SecurePass123!@#')
        cache.clear()

    @override_settings(PASSWORD_MAX_AGE_DAYS=30)
    def test_fresh_password_no_redirect(self):
        self.user.profile.password_changed_at = timezone.now()
        self.user.profile.save()

        response = self.client.get('/expenses/')
        assert response.status_code == 200

    @override_settings(PASSWORD_MAX_AGE_DAYS=30)
    def test_expired_password_redirects_to_settings(self):
        self.user.profile.password_changed_at = timezone.now() - timedelta(days=31)
        self.user.profile.save()

        response = self.client.get('/expenses/')
        assert response.status_code == 302
        assert '/auth/settings' in response.url

    @override_settings(PASSWORD_MAX_AGE_DAYS=0)
    def test_disabled_policy_no_redirect(self):
        self.user.profile.password_changed_at = timezone.now() - timedelta(days=9999)
        self.user.profile.save()

        response = self.client.get('/expenses/')
        assert response.status_code == 200

    @override_settings(PASSWORD_MAX_AGE_DAYS=30)
    def test_settings_page_exempt_from_redirect(self):
        self.user.profile.password_changed_at = timezone.now() - timedelta(days=31)
        self.user.profile.save()

        response = self.client.get('/auth/settings/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestComplexityValidator:

    def test_rejects_no_uppercase(self):
        from a_customeauth.validators import ComplexityValidator
        v = ComplexityValidator()
        with pytest.raises(ValidationError):
            v.validate('lowercase123!@#')

    def test_rejects_no_lowercase(self):
        from a_customeauth.validators import ComplexityValidator
        v = ComplexityValidator()
        with pytest.raises(ValidationError):
            v.validate('UPPERCASE123!@#')

    def test_rejects_no_digit(self):
        from a_customeauth.validators import ComplexityValidator
        v = ComplexityValidator()
        with pytest.raises(ValidationError):
            v.validate('NoDigitsHere!@#')

    def test_rejects_no_special(self):
        from a_customeauth.validators import ComplexityValidator
        v = ComplexityValidator()
        with pytest.raises(ValidationError):
            v.validate('NoSpecial123abc')

    def test_accepts_valid_password(self):
        from a_customeauth.validators import ComplexityValidator
        v = ComplexityValidator()
        v.validate('ValidPass123!@#')
