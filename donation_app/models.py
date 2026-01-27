from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from campaign.models import Campaign
from request_app import models as request_models
# Create your models here.
class Currency(models.TextChoices):
    INR = "INR", "INR"
    USD = "USD", "USD"
    EUR = "EUR", "EUR"

class Donation(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.PROTECT, related_name="donations")
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
            models.Index(fields=["campaign", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=Decimal("0.00")),
                name="donation_amount_positive",
            ),
        ]

    def clean(self):
        # enforce min/max per campaign
        if self.campaign:
            min_amt = self.campaign.minimum_donation_amount or Decimal("0.00")
            max_amt = self.campaign.maximum_donation_amount
            if self.amount < min_amt:
                raise ValueError(f"Donation must be at least {min_amt}.")
            if max_amt and self.amount > max_amt:
                raise ValueError(f"Donation must be at most {max_amt}.")

            # only allow donations to ACTIVE + PUBLIC campaigns
            if not (self.campaign.status() == request_models.RequestStatus.ACTIVE and self.campaign.visibility == Visibility.PUBLIC):
                raise ValueError("Donations are allowed only for ACTIVE and PUBLIC campaigns.")


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.campaign.title} - {self.amount} {self.currency}"
