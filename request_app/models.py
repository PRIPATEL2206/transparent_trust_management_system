from django.db import models
from django.conf import settings

# Create your models here.
class RequestedFor(models.TextChoices):
    CAMPAIGN = "CAMPAIGN", "Campaign"

class RequestStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    ACTIVE = "ACTIVE", "Active"
    CANCELED = "CANCELED", "Canceled"
    ARCHIVED = "ARCHIVED", "Archived"

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
    start_date=models.DateTimeField(auto_now_add=True)
    last_updated=models.DateTimeField(auto_now=True)
    requested_for = models.CharField(max_length=20, choices=RequestedFor.choices, default=RequestedFor.CAMPAIGN, db_index=True)
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.DRAFT,db_index=True)
    
    # update status
    def approve(self,user):
        if not self.can_approve(user):
            raise Exception("You don't have permission to approve this request")
        RequestMessage.objects.create(request=self,sender=user,massges=f"{RequestStatus[self.status]} -> APPROVED")
        self.status=RequestStatus.APPROVED
        self.reviewed_by=user
        self.save()
    def reject(self,user):
        if not self.can_approve(user):
            raise Exception("You don't have permission to reject this request")
        RequestMessage.objects.create(request=self,sender=user,massges=f"{self.status} -> REJECTED")
        self.status=RequestStatus.REJECTED
        self.save()
    def cancel(self,user):
        if not self.can_cancel(user):
            raise Exception("You don't have permission to cancel this request")
        RequestMessage.objects.create(request=self,sender=user,massges=f"{self.status} -> CANCELED")
        self.status=RequestStatus.CANCELED
        self.save()
    def send_for_review(self,user):
        if not self.can_send_for_review(user):
            raise Exception("You don't have permission to send this request for review")
        RequestMessage.objects.create(request=self,sender=user,massges=f"{self.status} -> PENDING_REVIEW")
        self.status=RequestStatus.PENDING_REVIEW
        self.save()
    def send_for_draft(self,user):
        if not self.can_draft(user):
            raise Exception("You don't have permission to send this request to draft")
        RequestMessage.objects.create(request=self,sender=user,massges=f"{self.status} -> DRAFT")
        self.status=RequestStatus.DRAFT
        self.save()
    

    def can_approve(self, user):
        return  user.is_approval_user and self.status in (RequestStatus.PENDING_REVIEW)
    def can_reject(self, user):
        return  user.is_approval_user and self.status in (RequestStatus.PENDING_REVIEW)
    def can_cancel(self, user):
        return  self.proposed_by == user and self.status  in (RequestStatus.PENDING_REVIEW,RequestStatus.DRAFT)
    def can_chat(self, user):
        return (user.is_approval_user or self.proposed_by == user) and self.status  in (RequestStatus.PENDING_REVIEW,RequestStatus.DRAFT)
    def can_send_for_review(self, user):
        return self.proposed_by == user and self.status in (RequestStatus.DRAFT)
    def can_draft(self, user):
        return self.proposed_by == user and self.status in (RequestStatus.PENDING_REVIEW)
    

    def is_draft(self):
        return self.status==RequestStatus.DRAFT
        