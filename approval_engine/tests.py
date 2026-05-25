from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from .models import ApprovalRequest
from .services import ApprovalService
from roles.models import UserRole
from services.exceptions import NotFoundError, ValidationError, PermissionDeniedError


class ApprovalServiceTests(TestCase):

    def setUp(self):
        self.requester = User.objects.create_user(username='requester', password='testpass')
        self.reviewer = User.objects.create_user(username='reviewer', password='testpass')
        self.user_role = UserRole.objects.get(user=self.requester)

    def test_submit_for_approval(self):
        approval = ApprovalService.submit_for_approval(self.user_role, self.requester)
        self.assertIsNotNone(approval)
        self.assertEqual(approval.status, 'pending')
        self.assertEqual(approval.requested_by, self.requester)
        self.assertEqual(approval.object_id, self.user_role.pk)

    def test_submit_for_approval_idempotent(self):
        a1 = ApprovalService.submit_for_approval(self.user_role, self.requester)
        a2 = ApprovalService.submit_for_approval(self.user_role, self.requester)
        self.assertEqual(a1.id, a2.id)

    def test_approve(self):
        approval = ApprovalService.submit_for_approval(self.user_role, self.requester)
        result = ApprovalService.approve(approval.id, self.reviewer, notes='Looks good')
        self.assertEqual(result.status, 'approved')
        self.assertEqual(result.reviewed_by, self.reviewer)
        self.assertEqual(result.notes, 'Looks good')
        self.assertIsNotNone(result.reviewed_at)

    def test_approve_nonexistent_raises(self):
        with self.assertRaises(Exception):
            ApprovalService.approve(99999, self.reviewer)

    def test_approve_already_processed_raises(self):
        approval = ApprovalService.submit_for_approval(self.user_role, self.requester)
        ApprovalService.approve(approval.id, self.reviewer)
        with self.assertRaises(Exception):
            ApprovalService.approve(approval.id, self.reviewer)

    def test_cannot_approve_own_request(self):
        approval = ApprovalService.submit_for_approval(self.user_role, self.requester)
        with self.assertRaises(Exception):
            ApprovalService.approve(approval.id, self.requester)

    def test_reject(self):
        approval = ApprovalService.submit_for_approval(self.user_role, self.requester)
        result = ApprovalService.reject(approval.id, self.reviewer, notes='Not eligible')
        self.assertEqual(result.status, 'rejected')
        self.assertEqual(result.reviewed_by, self.reviewer)
        self.assertEqual(result.notes, 'Not eligible')

    def test_get_pending(self):
        ApprovalService.submit_for_approval(self.user_role, self.requester)
        pending = ApprovalService.get_pending()
        self.assertEqual(pending.count(), 1)

    def test_get_pending_filtered(self):
        ApprovalService.submit_for_approval(self.user_role, self.requester)
        pending = ApprovalService.get_pending(content_type_model='userrole')
        self.assertEqual(pending.count(), 1)
        pending_other = ApprovalService.get_pending(content_type_model='user')
        self.assertEqual(pending_other.count(), 0)

    def test_is_approved(self):
        self.assertFalse(ApprovalService.is_approved(self.user_role))
        approval = ApprovalService.submit_for_approval(self.user_role, self.requester)
        ApprovalService.approve(approval.id, self.reviewer)
        self.assertTrue(ApprovalService.is_approved(self.user_role))

    def test_get_for_object(self):
        ApprovalService.submit_for_approval(self.user_role, self.requester)
        results = ApprovalService.get_for_object(self.user_role)
        self.assertEqual(results.count(), 1)
