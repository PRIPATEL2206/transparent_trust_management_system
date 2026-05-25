from django.test import TestCase
from django.contrib.auth.models import User

from .models import UserRole, RolePermission
from .services import RoleService, ROLE_HIERARCHY
from services.exceptions import ValidationError


class RoleServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.admin = User.objects.create_user(username='adminuser', password='testpass')
        UserRole.objects.filter(user=self.admin).update(role='admin', approved=True)
        self.admin.refresh_from_db()

    def test_get_user_role_default(self):
        role = RoleService.get_user_role(self.user)
        self.assertEqual(role, 'user')

    def test_get_user_role_after_assignment(self):
        RoleService.assign_role(self.user, 'member', approved_by=self.admin)
        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(RoleService.get_user_role(user), 'member')

    def test_assign_role_valid(self):
        user_role = RoleService.assign_role(self.user, 'member', approved_by=self.admin)
        self.assertEqual(user_role.role, 'member')
        self.assertTrue(user_role.approved)
        self.assertEqual(user_role.approved_by, self.admin)

    def test_assign_role_invalid_raises(self):
        with self.assertRaises(Exception):
            RoleService.assign_role(self.user, 'nonexistent_role', approved_by=self.admin)

    def test_assign_role_without_approver(self):
        user_role = RoleService.assign_role(self.user, 'member')
        self.assertFalse(user_role.approved)
        self.assertIsNone(user_role.approved_by)

    def test_has_permission_default(self):
        self.assertTrue(RoleService.has_permission(self.user, 'view_donations'))
        self.assertFalse(RoleService.has_permission(self.user, 'manage_roles'))

    def test_has_permission_with_custom_permission(self):
        RolePermission.objects.create(role='user', permission='custom_perm')
        self.assertTrue(RoleService.has_permission(self.user, 'custom_perm'))

    def test_has_role(self):
        self.assertTrue(RoleService.has_role(self.user, 'user'))
        self.assertFalse(RoleService.has_role(self.user, 'admin'))
        admin = User.objects.get(pk=self.admin.pk)
        self.assertTrue(RoleService.has_role(admin, 'admin', 'super_admin'))

    def test_can_manage_role_hierarchy(self):
        super_admin = User.objects.create_user(username='superadmin', password='testpass')
        UserRole.objects.filter(user=super_admin).update(role='super_admin')
        super_admin = User.objects.get(pk=super_admin.pk)
        admin = User.objects.get(pk=self.admin.pk)

        self.assertTrue(RoleService.can_manage_role(super_admin, 'admin'))
        self.assertTrue(RoleService.can_manage_role(super_admin, 'member'))
        self.assertFalse(RoleService.can_manage_role(admin, 'super_admin'))
        self.assertFalse(RoleService.can_manage_role(admin, 'admin'))
        self.assertTrue(RoleService.can_manage_role(admin, 'member'))

    def test_get_users_by_role(self):
        users = RoleService.get_users_by_role('admin')
        self.assertIn(self.admin, users)
        self.assertNotIn(self.user, users)

    def test_get_or_create_role(self):
        new_user = User.objects.create_user(username='newuser', password='pass')
        UserRole.objects.filter(user=new_user).delete()
        role = RoleService.get_or_create_role(new_user)
        self.assertEqual(role.role, 'user')
        self.assertEqual(role.user, new_user)

    def test_get_role_hierarchy(self):
        hierarchy = RoleService.get_role_hierarchy()
        self.assertEqual(hierarchy, ROLE_HIERARCHY)
        self.assertGreater(hierarchy['super_admin'], hierarchy['admin'])
        self.assertGreater(hierarchy['admin'], hierarchy['member'])
