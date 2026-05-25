from django.db import models
from django.contrib.auth.models import User


class UserRole(models.Model):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('user', 'User'),
        ('ngo', 'NGO'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='role_approvals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    @property
    def is_admin_or_above(self):
        return self.role in ('admin', 'super_admin')

    @property
    def is_super_admin(self):
        return self.role == 'super_admin'


class RolePermission(models.Model):
    role = models.CharField(max_length=20, choices=UserRole.ROLE_CHOICES)
    permission = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('role', 'permission')
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'

    def __str__(self):
        return f"{self.role} → {self.permission}"


class RoleRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_requests')
    requested_role = models.CharField(max_length=20, choices=UserRole.ROLE_CHOICES)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_role_requests'
    )
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.requested_role} ({self.status})"
