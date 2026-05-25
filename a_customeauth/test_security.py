from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User

from roles.models import UserRole


class OpenRedirectPreventionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()

    def test_login_redirect_to_internal_url(self):
        response = self.client.post('/auth/login/?next=/expenses/', {
            'username': 'testuser', 'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/expenses/')

    def test_login_blocks_external_redirect(self):
        response = self.client.post('/auth/login/?next=https://evil.com/', {
            'username': 'testuser', 'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_login_blocks_protocol_relative_redirect(self):
        response = self.client.post('/auth/login/?next=//evil.com/', {
            'username': 'testuser', 'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')


class LogoutPostOnlyTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_logout_get_returns_405(self):
        response = self.client.get('/auth/logout/')
        self.assertEqual(response.status_code, 405)

    def test_logout_post_succeeds(self):
        response = self.client.post('/auth/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.url)


class RBACDecoratorTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='normaluser', password='testpass123')
        self.admin = User.objects.create_user(username='adminuser', password='testpass123')
        UserRole.objects.filter(user=self.admin).update(role='admin', approved=True)
        self.client = Client()

    def test_admin_page_blocked_for_normal_user(self):
        self.client.login(username='normaluser', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_admin_page_accessible_for_admin(self):
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_admin_response_has_noindex_header(self):
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.get('X-Robots-Tag'), 'noindex, nofollow')


class ProfileUniquenessTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='testpass123', email='user1@test.com')
        self.user2 = User.objects.create_user(username='user2', password='testpass123', email='user2@test.com')
        self.client = Client()
        self.client.login(username='user1', password='testpass123')

    def test_cannot_change_username_to_existing(self):
        response = self.client.post('/auth/profile/', {
            'username': 'user2',
            'email': 'user1@test.com',
            'first_name': '',
            'last_name': '',
        })
        self.assertEqual(response.status_code, 200)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'user1')

    def test_cannot_change_email_to_existing(self):
        response = self.client.post('/auth/profile/', {
            'username': 'user1',
            'email': 'user2@test.com',
            'first_name': '',
            'last_name': '',
        })
        self.assertEqual(response.status_code, 200)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, 'user1@test.com')


class SecurityHeadersTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_csp_header_present(self):
        response = self.client.get('/health/')
        self.assertIn('Content-Security-Policy', response)

    def test_referrer_policy_header(self):
        response = self.client.get('/health/')
        self.assertEqual(response['Referrer-Policy'], 'strict-origin-when-cross-origin')

    def test_permissions_policy_header(self):
        response = self.client.get('/health/')
        self.assertIn('camera=()', response['Permissions-Policy'])

    def test_coop_header(self):
        response = self.client.get('/health/')
        self.assertEqual(response['Cross-Origin-Opener-Policy'], 'same-origin')
