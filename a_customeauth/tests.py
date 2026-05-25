from django.test import TestCase, Client
from django.contrib.auth.models import User


class SmokeTestPublicURLs(TestCase):
    """Verify public endpoints return expected status codes."""

    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_health_check(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')

    def test_login_page(self):
        response = self.client.get('/auth/login/')
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        response = self.client.get('/auth/register/')
        self.assertEqual(response.status_code, 200)

    def test_transparency_page(self):
        response = self.client.get('/transparency/')
        self.assertEqual(response.status_code, 200)


class SmokeTestAuthenticatedURLs(TestCase):
    """Verify authenticated endpoints redirect or return 200."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123', email='test@test.com'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_donations_page(self):
        response = self.client.get('/donation/')
        self.assertEqual(response.status_code, 200)

    def test_notices_page(self):
        response = self.client.get('/notices/')
        self.assertEqual(response.status_code, 200)

    def test_expenses_page(self):
        response = self.client.get('/expenses/')
        self.assertEqual(response.status_code, 200)

    def test_products_page(self):
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200)

    def test_profile_page(self):
        response = self.client.get('/auth/profile/')
        self.assertEqual(response.status_code, 200)

    def test_settings_page(self):
        response = self.client.get('/auth/settings/')
        self.assertEqual(response.status_code, 200)


class SmokeTestProtectedURLs(TestCase):
    """Verify unauthenticated users are redirected to login."""

    def setUp(self):
        self.client = Client()

    def test_donations_redirects(self):
        response = self.client.get('/donation/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.url)

    def test_expenses_redirects(self):
        response = self.client.get('/expenses/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.url)

    def test_dashboard_redirects(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)
