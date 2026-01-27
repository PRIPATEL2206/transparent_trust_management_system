from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum, Count
from django.utils import timezone
from django.utils.text import slugify
import os

from request_app.models import Request

# -----------------------
# Taxonomy / Supporting
# -----------------------
class CampaignCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Visibility(models.TextChoices):
    PRIVATE = "PRIVATE", "Private"
    PUBLIC = "PUBLIC", "Public"

class CampaignManager(models.Manager):
    def active_public(self):
        """
        Campaigns currently visible to donors.
        """
        now = timezone.now()
        return (
            self.get_queryset()
            .filter(
                status=CampaignStatus.ACTIVE,
                visibility=Visibility.PUBLIC,
            )
            .filter(
                models.Q(start_date__lte=now)
                & (models.Q(end_date__isnull=True) | models.Q(end_date__gte=now))
            )
        )

class CampaignImages(models.Model):

    def _get_image_url(instance, filename):
        base, ext = os.path.splitext(filename)
        safe_filename = f"{base.strip().replace(' ', '_')}{ext}"

        return f"campaign/gallery/{instance.campaign.id}/{safe_filename}"

    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to=_get_image_url)

    def __str__(self):
        return f'{self.campaign.title} - {self.image}'

class Campaign(models.Model):

    def _get_image_url(instance, filename):
        base, ext = os.path.splitext(filename)
        safe_filename = f"{instance.slug}{ext}"
        return f"campaign/cover_image/{safe_filename}"
        
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(CampaignCategory, on_delete=models.SET_NULL, null=True, related_name="campaigns")
    tags = models.JSONField(default=list, blank=True)
    cover_image = models.ImageField(
        upload_to=_get_image_url,
        null=True,
        blank=True
    )
    # gallery = models.ForeignKey(CampaignImages, on_delete=models.CASCADE, null=True, blank=True)

    # Governance & workflow
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PRIVATE)
    
    request=models.OneToOneField(Request, on_delete=models.DO_NOTHING,related_name="campaign")
    

    # Dates & duration
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    timezone_name = models.CharField(max_length=50, default="Asia/Kolkata")

    # Funding & goals
    goal_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                      validators=[MinValueValidator(Decimal("0.00"))])
    minimum_donation_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("10.00"),
                                                  validators=[MinValueValidator(Decimal("0.00"))])
    maximum_donation_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                                  validators=[MinValueValidator(Decimal("0.00"))])

    objects = CampaignManager()

    class Meta:
        # ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["visibility"]),
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["category"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(minimum_donation_amount__gte=Decimal("0.00")),
                name="min_donation_non_negative",
            ),
        ]

    def __str__(self):
        return self.title

    # -----------------------
    # Derived metrics
    # -----------------------

    @property
    def status(self):
        return self.request.status

    @property
    def amount_raised(self) -> Decimal:
        total = self.donations.aggregate(total=Sum("amount")).get("total")
        return total or Decimal("0.00")

    @property
    def donor_count(self) -> int:
        count = self.donations.values("donor_id").distinct().aggregate(c=Count("donor_id")).get("c")
        return count or 0

    @property
    def is_in_active_window(self) -> bool:
        now = timezone.now()
        return (self.start_date <= now) and (self.end_date is None or self.end_date >= now)

    # -----------------------
    # Validation & lifecycle
    # -----------------------
    def clean(self):
        # slug
        if not self.slug:
            self.slug = slugify(self.title)

        # dates
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date.")

        # donation amounts
        if self.maximum_donation_amount and self.minimum_donation_amount:
            if self.maximum_donation_amount < self.minimum_donation_amount:
                raise ValueError("maximum_donation_amount must be >= minimum_donation_amount.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    # -----------------------
    # State transitions
    # -----------------------
    @transaction.atomic
    def submit_for_review(self, user):
        if self.status != CampaignStatus.DRAFT:
            raise ValueError("Only DRAFT campaigns can be submitted for review.")
        if user != self.proposed_by and not user.is_staff:
            raise PermissionError("Only proposer or admin can submit for review.")
        old = self.status
        self.status = CampaignStatus.PENDING_REVIEW
        self.review_notes = ""
        self.reviewed_by = None
        self.approval_date = None
        self.save()

    @transaction.atomic
    def review(self, admin_user, decision: str, notes: str = ""):
        if not getattr(admin_user, "is_staff", False):
            raise PermissionError("Only admins can review campaigns.")
        if self.status != CampaignStatus.PENDING_REVIEW:
            raise ValueError("Only campaigns in PENDING_REVIEW can be reviewed.")

        decision = decision.upper()
        if decision not in (CampaignStatus.APPROVED, CampaignStatus.REJECTED):
            raise ValueError("Decision must be APPROVED or REJECTED.")

        old = self.status
        self.reviewed_by = admin_user
        self.review_notes = notes or ""
        if decision == CampaignStatus.APPROVED:
            self.status = CampaignStatus.APPROVED
            self.approval_date = timezone.now()
            # Auto publish if window is active
            if self.is_in_active_window and self.visibility == Visibility.PUBLIC:
                self.status = CampaignStatus.ACTIVE
                self.published_at = timezone.now()
        else:
            self.status = CampaignStatus.REJECTED
            self.approval_date = None

        self.save()

    @transaction.atomic
    def activate_if_ready(self, admin_user=None):
        """
        Move APPROVED -> ACTIVE when start_date arrives.
        Can be called by a cron or admin action.
        """
        if self.status in (CampaignStatus.APPROVED, CampaignStatus.CANCEL):
            if self.is_in_active_window:
                old = self.status
                self.status = CampaignStatus.ACTIVE
                self.published_at = self.published_at or timezone.now()
                self.save()

    @transaction.atomic
    def pause(self, admin_user, reason: str = ""):
        if not getattr(admin_user, "is_staff", False):
            raise PermissionError("Only admins can pause Campaigns.")
        if self.status != CampaignStatus.ACTIVE:
            raise ValueError("Only ACTIVE Campaigns can be paused.")
        old = self.status
        self.status = CampaignStatus.CANCEL
        self.save()

    @transaction.atomic
    def archive(self, admin_user, reason: str = ""):
        if not getattr(admin_user, "is_staff", False):
            raise PermissionError("Only admins can archive Campaigns.")
        if self.status in (CampaignStatus.ARCHIVED, CampaignStatus.REJECTED):
            raise ValueError("Cannot archive already archived or rejected Campaigns.")
        old = self.status
        self.status = CampaignStatus.ARCHIVED
        self.archived_at = timezone.now()
        self.save()
