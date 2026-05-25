from django.db import models
from django.contrib.auth.models import User


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Expense Categories'

    def __str__(self):
        return self.name


class Expense(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]

    raised_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    receipt = models.FileField(upload_to='expense_receipts/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    approved_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_expenses'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['raised_by', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.amount}"
