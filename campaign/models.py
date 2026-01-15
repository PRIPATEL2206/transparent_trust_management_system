
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


# -----------------------
# Taxonomy / Supporting
# -----------------------
class SchemeCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class SchemeStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    ACTIVE = "ACTIVE", "Active"
    PAUSED = "PAUSED", "Paused"
    ARCHIVED = "ARCHIVED", "Archived"

class Visibility(models.TextChoices):
    PRIVATE = "PRIVATE", "Private"
    PUBLIC = "PUBLIC", "Public"

class SchemeManager(models.Manager):
    def active_public(self):
        """
        Schemes currently visible to donors.
        """
        now = timezone.now()
        return (
            self.get_queryset()
            .filter(
                status=SchemeStatus.ACTIVE,
                visibility=Visibility.PUBLIC,
            )
            .filter(
                models.Q(start_date__lte=now)
                & (models.Q(end_date__isnull=True) | models.Q(end_date__gte=now))
            )
        )

class SchemeImages(models.Model):

    def _get_image_url(instance, filename):
        base, ext = os.path.splitext(filename)
        safe_filename = f"{base.strip().replace(' ', '_')}{ext}"

        return f"scheme/gallery/{instance.scheme.id}/{safe_filename}"

    scheme = models.ForeignKey('Scheme', on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to=_get_image_url)

    def __str__(self):
        return f'{self.scheme.title} - {self.image}'

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

class Scheme(models.Model):

    def _get_image_url(instance, filename):
        base, ext = os.path.splitext(filename)
        safe_filename = f"{instance.slug}{ext}"
        return f"scheme/cover_image/{safe_filename}"
        
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(SchemeCategory, on_delete=models.SET_NULL, null=True, related_name="schemes")
    tags = models.JSONField(default=list, blank=True)
    cover_image = models.ImageField(
        upload_to=_get_image_url,
        null=True,
        blank=True
    )
    # gallery = models.ForeignKey(SchemeImages, on_delete=models.CASCADE, null=True, blank=True)

    # Governance & workflow
    status = models.CharField(max_length=20, choices=SchemeStatus.choices, default=SchemeStatus.DRAFT, db_index=True)
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PRIVATE)
    
    request=models.ForeignKey('Request', on_delete=models.DO_NOTHING,related_name="schemes")
    

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

    objects = SchemeManager()

    class Meta:
        # ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "visibility"]),
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
        if self.status != SchemeStatus.DRAFT:
            raise ValueError("Only DRAFT schemes can be submitted for review.")
        if user != self.proposed_by and not user.is_staff:
            raise PermissionError("Only proposer or admin can submit for review.")
        old = self.status
        self.status = SchemeStatus.PENDING_REVIEW
        self.review_notes = ""
        self.reviewed_by = None
        self.approval_date = None
        self.save()
        SchemeStatusLog.log(self, old, self.status, user, "Submitted for review")

    @transaction.atomic
    def review(self, admin_user, decision: str, notes: str = ""):
        if not getattr(admin_user, "is_staff", False):
            raise PermissionError("Only admins can review schemes.")
        if self.status != SchemeStatus.PENDING_REVIEW:
            raise ValueError("Only schemes in PENDING_REVIEW can be reviewed.")

        decision = decision.upper()
        if decision not in (SchemeStatus.APPROVED, SchemeStatus.REJECTED):
            raise ValueError("Decision must be APPROVED or REJECTED.")

        old = self.status
        self.reviewed_by = admin_user
        self.review_notes = notes or ""
        if decision == SchemeStatus.APPROVED:
            self.status = SchemeStatus.APPROVED
            self.approval_date = timezone.now()
            # Auto publish if window is active
            if self.is_in_active_window and self.visibility == Visibility.PUBLIC:
                self.status = SchemeStatus.ACTIVE
                self.published_at = timezone.now()
        else:
            self.status = SchemeStatus.REJECTED
            self.approval_date = None

        self.save()
        SchemeStatusLog.log(self, old, self.status, admin_user, f"Review: {decision}")

    @transaction.atomic
    def activate_if_ready(self, admin_user=None):
        """
        Move APPROVED -> ACTIVE when start_date arrives.
        Can be called by a cron or admin action.
        """
        if self.status in (SchemeStatus.APPROVED, SchemeStatus.PAUSED):
            if self.is_in_active_window:
                old = self.status
                self.status = SchemeStatus.ACTIVE
                self.published_at = self.published_at or timezone.now()
                self.save()
                SchemeStatusLog.log(self, old, self.status, admin_user, "Auto-activated")

    @transaction.atomic
    def pause(self, admin_user, reason: str = ""):
        if not getattr(admin_user, "is_staff", False):
            raise PermissionError("Only admins can pause schemes.")
        if self.status != SchemeStatus.ACTIVE:
            raise ValueError("Only ACTIVE schemes can be paused.")
        old = self.status
        self.status = SchemeStatus.PAUSED
        self.save()
        SchemeStatusLog.log(self, old, self.status, admin_user, reason or "Paused")

    @transaction.atomic
    def archive(self, admin_user, reason: str = ""):
        if not getattr(admin_user, "is_staff", False):
            raise PermissionError("Only admins can archive schemes.")
        if self.status in (SchemeStatus.ARCHIVED, SchemeStatus.REJECTED):
            raise ValueError("Cannot archive already archived or rejected schemes.")
        old = self.status
        self.status = SchemeStatus.ARCHIVED
        self.archived_at = timezone.now()
        self.save()
        SchemeStatusLog.log(self, old, self.status, admin_user, reason or "Archived")

class Currency(models.TextChoices):
    INR = "INR", "INR"
    USD = "USD", "USD"
    EUR = "EUR", "EUR"

class Donation(models.Model):
    scheme = models.ForeignKey(Scheme, on_delete=models.PROTECT, related_name="donations")
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="donations",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=10, choices=Currency.choices, default=Currency.INR)
    dispaly_name = models.CharField(max_length=100, blank=True)
    donor_display_name = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["scheme", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=Decimal("0.00")),
                name="donation_amount_positive",
            ),
        ]

    def clean(self):
        # enforce min/max per scheme
        if self.scheme:
            min_amt = self.scheme.minimum_donation_amount or Decimal("0.00")
            max_amt = self.scheme.maximum_donation_amount
            if self.amount < min_amt:
                raise ValueError(f"Donation must be at least {min_amt}.")
            if max_amt and self.amount > max_amt:
                raise ValueError(f"Donation must be at most {max_amt}.")

            # only allow donations to ACTIVE + PUBLIC schemes
            if not (self.scheme.status == SchemeStatus.ACTIVE and self.scheme.visibility == Visibility.PUBLIC):
                raise ValueError("Donations are allowed only for ACTIVE and PUBLIC schemes.")

            # recurring frequency presence check
            if self.is_recurring and not self.recurring_frequency:
                raise ValueError("recurring_frequency is required for recurring donations.")
            if (not self.is_recurring) and self.recurring_frequency:
                raise ValueError("recurring_frequency should be null if is_recurring is False.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.scheme.title} - {self.amount} {self.currency}"
