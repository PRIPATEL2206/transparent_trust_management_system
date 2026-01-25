from django.db import models
from django.conf import settings

# Create your models here.

class RequestMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,related_name="sent_messages")
    request=models.ForeignKey('Request', on_delete=models.CASCADE,related_name="messages")
    massges = models.CharField(max_length=200)
    sent_at = models.DateTimeField(auto_now_add=True)

class Request(models.Model):
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requests",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewes",
    )
    request_start_date=models.DateTimeField(auto_now_add=True)
    request_end_date=models.DateTimeField(blank=True,null=True)

    def can_approve(self, user):
        print("-------------------",user.is_approval_user)
        return user.is_approval_user
    def can_cancel(self, user):
        return user.is_approval_user or self.proposed_by == user
    def can_chat(self, user):
        return user.is_approval_user or self.proposed_by == user
        