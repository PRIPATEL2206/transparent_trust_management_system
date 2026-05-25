from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class NoticeManager(models.Manager):
    def active(self):
        now = timezone.now()
        return self.filter(
            is_approved=True,
            is_active=True
        ).exclude(
            expires_at__lt=now
        )


class Notice(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notices')
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NoticeManager()

    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['is_approved', 'is_active', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='info')
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"
