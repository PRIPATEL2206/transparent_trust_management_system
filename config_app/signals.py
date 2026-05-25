from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SiteConfig
from .services import ConfigService


@receiver(post_save, sender=SiteConfig)
def invalidate_config_cache(sender, **kwargs):
    ConfigService.invalidate_cache()
