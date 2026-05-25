from django.db import models
from django.contrib.auth.models import User


class ActivityLog(models.Model):
    CATEGORY_CHOICES = [
        ('auth', 'Authentication'),
        ('role', 'Role Management'),
        ('expense', 'Expense'),
        ('payment', 'Payment'),
        ('donation', 'Donation'),
        ('notice', 'Notice'),
        ('approval', 'Approval'),
        ('order', 'Order'),
        ('ngo', 'NGO Request'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='system')
    target_user = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='targeted_logs'
    )
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['category', '-created_at']),
        ]

    def __str__(self):
        username = self.user.username if self.user else 'anonymous'
        return f"{username} - {self.action} ({self.created_at:%Y-%m-%d %H:%M})"
