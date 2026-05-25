"""
Startup validation — runs once at process boot to catch misconfigurations early.

Called from entrypoint.sh via `python manage.py preflight` or auto-invoked by
AppConfig.ready() in production.
"""

import os
import sys
import logging

logger = logging.getLogger('services')


class StartupValidator:
    """Validates environment and dependencies at process startup."""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_all(self):
        self._check_secret_key()
        self._check_database_url()
        self._check_allowed_hosts()
        self._check_media_writable()
        self._check_required_directories()
        self._check_redis_connectivity()
        return self.errors, self.warnings

    def _check_secret_key(self):
        from django.conf import settings
        if not settings.DEBUG:
            key = settings.SECRET_KEY
            if 'insecure' in key or len(key) < 32:
                self.errors.append(
                    'SECRET_KEY is insecure or too short for production. '
                    'Set DJANGO_SECRET_KEY to a random 50+ character string.'
                )

    def _check_database_url(self):
        from django.conf import settings
        db = settings.DATABASES.get('default', {})
        if not settings.DEBUG and 'sqlite' in db.get('ENGINE', ''):
            self.warnings.append(
                'SQLite in production is not recommended. '
                'Set DB_ENGINE=django.db.backends.postgresql'
            )

    def _check_allowed_hosts(self):
        from django.conf import settings
        if not settings.DEBUG and '*' in settings.ALLOWED_HOSTS:
            self.errors.append(
                'ALLOWED_HOSTS contains wildcard (*) in production. '
                'Set DJANGO_ALLOWED_HOSTS to your actual domain(s).'
            )

    def _check_media_writable(self):
        from django.conf import settings
        media_root = str(settings.MEDIA_ROOT)
        if media_root and os.path.exists(media_root):
            if not os.access(media_root, os.W_OK):
                self.errors.append(
                    f'MEDIA_ROOT ({media_root}) is not writable. '
                    f'File uploads will fail.'
                )
        elif media_root and not os.path.exists(media_root):
            try:
                os.makedirs(media_root, exist_ok=True)
            except OSError as e:
                self.errors.append(f'Cannot create MEDIA_ROOT ({media_root}): {e}')

    def _check_required_directories(self):
        from django.conf import settings
        dirs = [
            settings.BASE_DIR / 'logs',
            settings.MEDIA_ROOT,
        ]
        for d in dirs:
            path = str(d)
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except OSError:
                    self.warnings.append(f'Could not create directory: {path}')

    def _check_redis_connectivity(self):
        from django.conf import settings
        if not settings.DEBUG:
            cache_backend = settings.CACHES.get('default', {}).get('BACKEND', '')
            if 'redis' in cache_backend.lower():
                try:
                    from django.core.cache import cache
                    cache.set('_startup_check', '1', 5)
                    if cache.get('_startup_check') != '1':
                        self.warnings.append('Redis cache set/get failed during startup check.')
                except Exception as e:
                    self.warnings.append(f'Redis connectivity check failed: {e}')


def run_startup_validation():
    validator = StartupValidator()
    errors, warnings = validator.validate_all()

    for w in warnings:
        logger.warning('[STARTUP] %s', w)

    if errors:
        for e in errors:
            logger.error('[STARTUP] %s', e)
        env = os.environ.get('DJANGO_ENV', 'development')
        if env == 'production':
            logger.critical(
                '[STARTUP] %d critical error(s) detected. '
                'Fix these before deploying to production.', len(errors)
            )
            sys.exit(1)
    else:
        logger.info('[STARTUP] All validation checks passed.')
