from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.urls import reverse
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum, Count
from django.utils import timezone
from django.utils.text import slugify
import os

from request_app.models import Request

from a_core.utils.storage import OverwriteStorage


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

    def delete(self, *args, **kwargs):
        self.image.delete()
        super().delete(*args, **kwargs)

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
        storage=OverwriteStorage(),
        null=True,
        blank=True
    )
    # gallery = models.ForeignKey(CampaignImages, on_delete=models.CASCADE, null=True, blank=True)

    # Governance & workflow
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PRIVATE)
    
    request=models.OneToOneField(Request, on_delete=models.DO_NOTHING,related_name="request_obj")
    

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

    def delete(self, *args, **kwargs):
        self.cover_image.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title

    # -----------------------
    # Derived metrics
    # -----------------------

    @property
    def status(self):
        return self.request.status
    
    @property
    def get_slug(self):
        return self.slug
    @property
    def get_title(self):
        return self.title
        
    @property
    def get_short_description(self):
        return self.short_description
        
    def get_absolute_url(self):
        return reverse('campaign:detail', kwargs={'slug': self.slug})

    @property
    def amount_raised(self) -> Decimal:
        cached = getattr(self, "_amount_raised", None)
        if cached is not None:
            return cached
        # Fallback compute
        return self.donations.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    
    @property
    def donations_count(self) -> int:
        cached = getattr(self, "_donations_count", None)
        if cached is not None:
            return cached
        return self.donations.count()


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

    def on_approve(self):
        self.visibility=Visibility.PUBLIC
        self.save()