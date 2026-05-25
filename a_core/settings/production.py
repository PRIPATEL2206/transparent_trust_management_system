from .base import *  # noqa: F401,F403
from .base import env


DEBUG = False

SECRET_KEY = env('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('DJANGO_SECRET_KEY must be set in production')

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError('DJANGO_ALLOWED_HOSTS must be set in production')

# =============================================================================
# PostgreSQL with connection pooling
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', 'trust_management'),
        'USER': env('DB_USER', 'postgres'),
        'PASSWORD': env('DB_PASSWORD', ''),
        'HOST': env('DB_HOST', 'localhost'),
        'PORT': env('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(env('DB_CONN_MAX_AGE', '600')),
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'connect_timeout': 5,
            'options': '-c statement_timeout=30000',
        },
    }
}

# =============================================================================
# Redis Cache
# =============================================================================
_redis_url = env('REDIS_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': _redis_url,
        'OPTIONS': {
            'socket_connect_timeout': 5,
            'socket_timeout': 5,
            'retry_on_timeout': True,
        },
        'KEY_PREFIX': 'trust',
        'TIMEOUT': 300,
    }
}

# =============================================================================
# Redis Channel Layer
# =============================================================================
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_URL', 'redis://localhost:6379/0')],
            'capacity': 1500,
            'expiry': 10,
        },
    }
}

# =============================================================================
# Session backend — use cached_db for speed + durability
# =============================================================================
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# =============================================================================
# Production Security
# =============================================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = '__Host-sessionid'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_NAME = '__Host-csrftoken'
SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT', 'True', cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# =============================================================================
# Email — production SMTP
# =============================================================================
EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

# =============================================================================
# Logging — JSON formatter in production
# =============================================================================
LOGGING['handlers']['console']['formatter'] = 'json'  # noqa: F405
LOGGING['handlers']['file']['formatter'] = 'json'  # noqa: F405
