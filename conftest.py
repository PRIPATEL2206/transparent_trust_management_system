import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user_data():
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePass123!@#',
    }


@pytest.fixture
def user(db, user_data):
    u = User.objects.create_user(
        username=user_data['username'],
        email=user_data['email'],
        password=user_data['password'],
    )
    return u


@pytest.fixture
def admin_user(db):
    u = User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='AdminPass123!@#',
    )
    from roles.models import UserRole
    role = UserRole.objects.get(user=u)
    role.role = 'admin'
    role.approved = True
    role.save()
    return u


@pytest.fixture
def super_admin_user(db):
    u = User.objects.create_superuser(
        username='superadmin',
        email='super@example.com',
        password='SuperPass123!@#',
    )
    from roles.models import UserRole
    role, _ = UserRole.objects.get_or_create(user=u, defaults={'role': 'super_admin', 'approved': True})
    role.role = 'super_admin'
    role.approved = True
    role.save()
    return u


@pytest.fixture
def authenticated_client(client, user, user_data):
    client.login(username=user_data['username'], password=user_data['password'])
    return client


@pytest.fixture
def admin_client(client, admin_user):
    client.login(username='adminuser', password='AdminPass123!@#')
    return client
