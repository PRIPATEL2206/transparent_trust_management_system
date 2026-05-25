from django.db import models
from django.contrib.auth.models import User


class GeneratedReport(models.Model):
    REPORT_TYPES = [
        ('donations', 'Donations'),
        ('expenses', 'Expenses'),
        ('transactions', 'Transactions'),
        ('members', 'Members'),
    ]
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
    ]

    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    format = models.CharField(max_length=5, choices=FORMAT_CHOICES)
    date_from = models.DateField()
    date_to = models.DateField()
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    file = models.FileField(upload_to='reports/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_report_type_display()} ({self.date_from} - {self.date_to})"
