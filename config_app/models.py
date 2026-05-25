from django.db import models


class SiteConfig(models.Model):
    trust_name = models.CharField(max_length=200, default='Trust Management System')
    trust_description = models.TextField(blank=True)

    membership_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    user_join_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_donation_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    meta_title = models.CharField(max_length=200, blank=True, default='Trust Management')
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)

    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    razorpay_key_id = models.CharField(max_length=100, blank=True)
    razorpay_key_secret = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Site Configuration'

    def __str__(self):
        return self.trust_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
