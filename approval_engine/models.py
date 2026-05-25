from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ApprovalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    requested_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='approval_requests'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_approvals'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status', 'created_at']),
        ]
        verbose_name = 'Approval Request'
        verbose_name_plural = 'Approval Requests'

    def __str__(self):
        return f"{self.content_type.model} #{self.object_id} - {self.get_status_display()}"

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_approved(self):
        return self.status == 'approved'
