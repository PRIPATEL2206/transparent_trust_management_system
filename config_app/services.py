from django.core.cache import cache

from services.base import BaseService
from .models import SiteConfig

CACHE_KEY = 'site_config'
CACHE_TIMEOUT = 300


class ConfigService(BaseService):

    @staticmethod
    def get_config() -> SiteConfig:
        config = cache.get(CACHE_KEY)
        if config is None:
            config = SiteConfig.get_instance()
            cache.set(CACHE_KEY, config, CACHE_TIMEOUT)
        return config

    @staticmethod
    def get(key: str, default=None):
        config = ConfigService.get_config()
        return getattr(config, key, default)

    @staticmethod
    def invalidate_cache():
        cache.delete(CACHE_KEY)
