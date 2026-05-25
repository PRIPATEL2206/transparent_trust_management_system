import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, RequestFactory

from roles.models import UserRole
from roles.services import RoleService
from roles.decorators import role_required, admin_required, permission_required
from services.exceptions import ValidationError


@pytest.mark.django_db
class TestRoleService:

    def setup_method(self):
        self.user = User.objects.create_user(
            username='roletest', password='SecurePass123!@#'
        )
        self.admin = User.objects.create_user(
            username='roleadmin', password='AdminPass123!@#'
        )
        cache.clear()

    def test_new_user_gets_user_role(self):
        role = RoleService.get_user_role(self.user)
        assert role == 'user'

    def test_assign_role_changes_role(self):
        RoleService.assign_role(self.user, 'member', approved_by=self.admin)
        assert RoleService.get_user_role(self.user) == 'member'

    def test_assign_role_sets_approved(self):
        user_role = RoleService.assign_role(self.user, 'member', approved_by=self.admin)
        assert user_role.approved is True
        assert user_role.approved_by == self.admin

    def test_assign_invalid_role_raises(self):
        with pytest.raises(ValidationError):
            RoleService.assign_role(self.user, 'invalid_role')

    def test_has_role_true(self):
        RoleService.assign_role(self.user, 'admin', approved_by=self.admin)
        assert RoleService.has_role(self.user, 'admin', 'super_admin') is True

    def test_has_role_false(self):
        assert RoleService.has_role(self.user, 'admin', 'super_admin') is False

    def test_has_permission_from_defaults(self):
        RoleService.assign_role(self.user, 'member', approved_by=self.admin)
        assert RoleService.has_permission(self.user, 'create_donations') is True
        assert RoleService.has_permission(self.user, 'manage_roles') is False

    def test_admin_has_manage_permissions(self):
        RoleService.assign_role(self.user, 'admin', approved_by=self.admin)
        assert RoleService.has_permission(self.user, 'approve_content') is True
        assert RoleService.has_permission(self.user, 'view_dashboard') is True

    def test_can_manage_role_hierarchy(self):
        RoleService.assign_role(self.admin, 'admin', approved_by=self.admin)
        assert RoleService.can_manage_role(self.admin, 'member') is True
        assert RoleService.can_manage_role(self.admin, 'admin') is False
        assert RoleService.can_manage_role(self.admin, 'super_admin') is False

    def test_get_users_by_role(self):
        RoleService.assign_role(self.user, 'member', approved_by=self.admin)
        members = RoleService.get_users_by_role('member')
        assert self.user in members


@pytest.mark.django_db
class TestRoleDecorators:

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='decuser', password='SecurePass123!@#'
        )
        self.admin = User.objects.create_user(
            username='decadmin', password='AdminPass123!@#'
        )
        admin_role = UserRole.objects.get(user=self.admin)
        admin_role.role = 'admin'
        admin_role.approved = True
        admin_role.save()
        cache.clear()

    def test_admin_required_blocks_normal_user(self):
        self.client.login(username='decuser', password='SecurePass123!@#')
        response = self.client.get('/dashboard/')
        assert response.status_code == 302
        assert response.url == '/'

    def test_admin_required_allows_admin(self):
        self.client.login(username='decadmin', password='AdminPass123!@#')
        response = self.client.get('/dashboard/')
        assert response.status_code == 200

    def test_admin_required_redirects_anonymous(self):
        response = self.client.get('/dashboard/')
        assert response.status_code == 302
        assert '/auth/login' in response.url

    def test_admin_response_has_noindex(self):
        self.client.login(username='decadmin', password='AdminPass123!@#')
        response = self.client.get('/dashboard/')
        assert response['X-Robots-Tag'] == 'noindex, nofollow'

    def test_role_required_blocks_wrong_role(self):
        self.client.login(username='decuser', password='SecurePass123!@#')
        response = self.client.get('/expenses/admin/')
        assert response.status_code == 302

    def test_role_required_allows_correct_role(self):
        self.client.login(username='decadmin', password='AdminPass123!@#')
        response = self.client.get('/expenses/admin/')
        assert response.status_code == 200
