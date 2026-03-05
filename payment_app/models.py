from django.db import models
from account.models import CustomUser

class PaymentStatus(models.TextChoices):
    SUCCESS = "SUCCESS", "Success"
    FAIL = "FAIL", "Fail"
    PENDING = "PENDING", "Pending"
    REFUNDED = "REFUNDED", "Refunded"

class PaymentFor(models.TextChoices):
    DONATIONS = "DONATIONS", "Donations"

# Create your models here.
class Payment(models.Model):
    user = models.ForeignKey(CustomUser,null=True, on_delete=models.SET_NULL)
    payment_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20,choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_for = models.CharField(max_length=20, choices=PaymentFor.choices, default=PaymentFor.DONATIONS, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)