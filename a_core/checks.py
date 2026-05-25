import os

from django.conf import settings
from django.core.checks import Warning, Error, register


@register()
def check_secret_key(app_configs, **kwargs):
    errors = []
    if 'insecure' in settings.SECRET_KEY and not settings.DEBUG:
        errors.append(
            Error(
                'You are using the default insecure SECRET_KEY in a non-DEBUG environment.',
                hint='Set the DJANGO_SECRET_KEY environment variable to a unique, unpredictable value.',
                id='a_core.E001',
            )
        )
    if not settings.DEBUG and '*' in settings.ALLOWED_HOSTS:
        errors.append(
            Error(
                'ALLOWED_HOSTS contains wildcard in production. This is a security vulnerability.',
                hint='Set DJANGO_ALLOWED_HOSTS to your actual domain(s).',
                id='a_core.E002',
            )
        )
    elif settings.DEBUG and settings.ALLOWED_HOSTS == ['*']:
        errors.append(
            Warning(
                'ALLOWED_HOSTS is set to wildcard. This is fine for local dev but must be restricted in production.',
                hint='Set DJANGO_ALLOWED_HOSTS to your actual domain(s).',
                id='a_core.W002',
            )
        )
    return errors


@register()
def check_production_config(app_configs, **kwargs):
    errors = []
    if not settings.DEBUG:
        if not os.environ.get('EMAIL_HOST_USER'):
            errors.append(
                Warning(
                    'EMAIL_HOST_USER not set. Password reset emails will not be delivered.',
                    hint='Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD for transactional email.',
                    id='a_core.W003',
                )
            )
        if settings.CACHES['default']['BACKEND'] == 'django.core.cache.backends.locmem.LocMemCache':
            errors.append(
                Warning(
                    'Using in-memory cache in production. Cache is not shared across workers.',
                    hint='Set CACHE_BACKEND to django.core.cache.backends.redis.RedisCache and REDIS_URL.',
                    id='a_core.W004',
                )
            )
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            errors.append(
                Warning(
                    'Using SQLite in production. Not recommended for concurrent multi-user access.',
                    hint='Set DB_ENGINE to django.db.backends.postgresql for production.',
                    id='a_core.W005',
                )
            )
        if not os.environ.get('DJANGO_SECRET_KEY'):
            errors.append(
                Error(
                    'DJANGO_SECRET_KEY not set via environment variable in production.',
                    hint='Generate a strong secret key: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"',
                    id='a_core.E003',
                )
            )
        channel_backend = settings.CHANNEL_LAYERS.get('default', {}).get('BACKEND', '')
        if 'InMemoryChannelLayer' in channel_backend:
            errors.append(
                Warning(
                    'Using InMemoryChannelLayer in production. WebSocket messages are not shared across workers.',
                    hint='Set CHANNEL_BACKEND to channels_redis.core.RedisChannelLayer.',
                    id='a_core.W006',
                )
            )
    return errors


@register()
def check_file_permissions(app_configs, **kwargs):
    errors = []
    media_dir = settings.MEDIA_ROOT
    if media_dir and os.path.exists(media_dir):
        if os.access(media_dir, os.W_OK) is False:
            errors.append(
                Error(
                    f'MEDIA_ROOT ({media_dir}) is not writable. File uploads will fail.',
                    hint='Fix permissions: chmod 755 on the media directory.',
                    id='a_core.E004',
                )
            )
    logs_dir = settings.BASE_DIR / 'logs'
    if logs_dir.exists() and not os.access(logs_dir, os.W_OK):
        errors.append(
            Error(
                f'Logs directory ({logs_dir}) is not writable.',
                hint='Fix permissions on the logs directory.',
                id='a_core.E005',
            )
        )
    return errors
