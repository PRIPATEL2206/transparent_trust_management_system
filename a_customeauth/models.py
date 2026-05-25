import uuid
import secrets
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

BASE_PROFILE_UPLOAD = "profiles/"

def get_upload_url(profile,filename:str):
    return BASE_PROFILE_UPLOAD + str(profile.user.id) + "." + filename.split('.')[-1]


class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    avatar = models.ImageField(upload_to=get_upload_url,null=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)

    def get_avatar_url(self):
        return self.avatar.url if self.avatar else '/media/profiles/defult_profile_image.jpg'
    def __str__(self):
        return self.user.username


class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=300, blank=True)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        status = 'OK' if self.success else 'FAIL'
        return f"{self.user.username} [{status}] {self.ip_address} @ {self.created_at:%Y-%m-%d %H:%M}"


class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    resend_count = models.PositiveIntegerField(default=0)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['token']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def regenerate_token(self):
        self.token = uuid.uuid4()
        self.expires_at = timezone.now() + timedelta(hours=24)
        self.resend_count += 1
        self.last_sent_at = timezone.now()
        self.save()

    def verify(self):
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save()

    def __str__(self):
        status = 'verified' if self.is_verified else 'pending'
        return f"{self.user.username} [{status}]"


class TOTPDevice(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='totp_device')
    secret = models.CharField(max_length=64)
    is_active = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)
    backup_codes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def generate_backup_codes(self):
        codes = [secrets.token_hex(4) for _ in range(8)]
        hashed = [hashlib.sha256(c.encode()).hexdigest() for c in codes]
        self.backup_codes = ','.join(hashed)
        self.save(update_fields=['backup_codes'])
        return codes

    def verify_backup_code(self, code):
        hashed_input = hashlib.sha256(code.strip().encode()).hexdigest()
        stored = self.backup_codes.split(',') if self.backup_codes else []
        if hashed_input in stored:
            stored.remove(hashed_input)
            self.backup_codes = ','.join(stored)
            self.save(update_fields=['backup_codes'])
            return True
        return False

    @property
    def backup_codes_remaining(self):
        if not self.backup_codes:
            return 0
        return len([c for c in self.backup_codes.split(',') if c])

    def __str__(self):
        status = 'active' if self.is_active else 'inactive'
        return f"{self.user.username} TOTP [{status}]"