import os
from pathlib import Path


def env(key, default=None, cast=None):
    value = os.environ.get(key, default)
    if value is None:
        return None
    if cast is bool:
        return value.lower() in ('true', '1', 'yes')
    if cast is int:
        return int(value)
    return value


BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env('DJANGO_SECRET_KEY', 'django-insecure-t=@j3za4^1@12i@h0il-uw+(zip6-)y3w@)98$vw8u0k5xtsn-')

DEBUG = env('DJANGO_DEBUG', 'True', cast=bool)

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS', '*').split(',')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Existing apps
    'a_customeauth',
    'donations',
    # Phase 1: Foundation
    'roles',
    'config_app',
    'approval_engine',
    # Phase 2: Core Business
    'expenses',
    'payments',
    'notices',
    # Phase 3: Analytics
    'dashboard',
    'reports',
    'transparency',
    # Phase 4: Extensions
    'chat',
    'products',
    'ngo_requests',
]

MIDDLEWARE = [
    'services.middleware.RequestIDMiddleware',
    'services.middleware.RequestBodySizeMiddleware',
    'services.middleware.GlobalThrottleMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'services.middleware.ServiceErrorMiddleware',
    'services.middleware.RequestTimingMiddleware',
    'services.middleware.SecurityHeadersMiddleware',
    'services.middleware.IdleSessionTimeoutMiddleware',
    'services.middleware.AdminIPPinMiddleware',
    'services.middleware.OriginCheckMiddleware',
    'services.middleware.MediaContentTypeMiddleware',
    'services.middleware.PasswordAgeMiddleware',
    'services.cors.CORSMiddleware',
    'services.metrics.MetricsMiddleware',
]

ROOT_URLCONF = 'a_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config_app.context_processors.site_config_context',
                'notices.context_processors.notifications_context',
                'a_customeauth.context_processors.email_verification_context',
                'services.context_processors.csp_nonce',
            ],
        },
    },
]

WSGI_APPLICATION = 'a_core.wsgi.application'

# Database — default SQLite, overridden in production
DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': env('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
        'USER': env('DB_USER', ''),
        'PASSWORD': env('DB_PASSWORD', ''),
        'HOST': env('DB_HOST', ''),
        'PORT': env('DB_PORT', ''),
        'CONN_MAX_AGE': int(env('DB_CONN_MAX_AGE', '600')),
        'CONN_HEALTH_CHECKS': True,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'a_customeauth.validators.ComplexityValidator'},
    {'NAME': 'a_customeauth.validators.BreachedPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('TZ', 'UTC')
USE_I18N = True
USE_TZ = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'auth_login'
CSRF_FAILURE_VIEW = 'a_core.error_handlers.csrf_failure'

# Cache — default LocMem, overridden per environment
_cache_backend = env('CACHE_BACKEND', 'django.core.cache.backends.locmem.LocMemCache')
_redis_url = env('REDIS_URL', 'redis://localhost:6379/0')

if 'redis' in _cache_backend.lower():
    CACHES = {
        'default': {
            'BACKEND': _cache_backend,
            'LOCATION': _redis_url,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': _cache_backend,
            'LOCATION': 'trust-mgmt-cache',
        }
    }

# Django Channels (WebSocket chat)
ASGI_APPLICATION = 'a_core.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': env('CHANNEL_BACKEND', 'channels.layers.InMemoryChannelLayer'),
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'sensitive': {
            '()': 'services.logging.SensitiveFilter',
        },
        'request_context': {
            '()': 'services.logging.RequestContextFilter',
        },
    },
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message} [rid={request_id} user={user} ip={ip}]',
            'style': '{',
        },
        'json': {
            '()': 'services.logging.JSONFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if not DEBUG else 'verbose',
            'filters': ['sensitive', 'request_context'],
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'formatter': 'json' if not DEBUG else 'verbose',
            'filters': ['sensitive', 'request_context'],
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
        },
        'audit_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'formatter': 'json',
            'filters': ['request_context'],
            'maxBytes': 50 * 1024 * 1024,
            'backupCount': 10,
        },
    },
    'loggers': {
        'services': {
            'handlers': ['console', 'file'],
            'level': env('LOG_LEVEL', 'INFO'),
        },
        'audit': {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'django.security': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
    },
}

# Create logs directory
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# File upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Session security
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 hours
SESSION_IDLE_TIMEOUT = int(env('SESSION_IDLE_TIMEOUT', '1800'))
SESSION_MAX_AGE = int(env('SESSION_MAX_AGE', '86400'))
MAX_SESSIONS_PER_USER = int(env('MAX_SESSIONS_PER_USER', '3'))
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True

# CSRF security
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
_csrf_origins = env('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]
if not CSRF_TRUSTED_ORIGINS and DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        'https://*.cloudworkstations.dev',
        'https://*.cluster-udxxdyopu5c7cwhhtg6mmadhvs.cloudworkstations.dev',
    ]

# Global request throttle (per IP)
THROTTLE_MAX_REQUESTS = int(env('THROTTLE_MAX_REQUESTS', '100'))
THROTTLE_WINDOW = int(env('THROTTLE_WINDOW', '60'))

# Health check API key
HEALTH_CHECK_API_KEY = env('HEALTH_CHECK_API_KEY', '')

# Email configuration
EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(env('EMAIL_PORT', '587'))
EMAIL_USE_TLS = env('EMAIL_USE_TLS', 'True', cast=bool)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'noreply@trustmanagement.org')

# CORS (for /api/ endpoints only)
API_PREFIX = '/api/'
CORS_ALLOWED_ORIGINS = [o.strip() for o in env('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()]
CORS_ALLOW_CREDENTIALS = env('CORS_ALLOW_CREDENTIALS', 'False', cast=bool)
CORS_MAX_AGE = 86400

# Password age policy (days before forced rotation; 0 = disabled)
PASSWORD_MAX_AGE_DAYS = int(env('PASSWORD_MAX_AGE_DAYS', '90'))

# Sentry error tracking
SENTRY_DSN = env('SENTRY_DSN', '')
SENTRY_TRACES_SAMPLE_RATE = env('SENTRY_TRACES_SAMPLE_RATE', '0.1')
SENTRY_PROFILES_SAMPLE_RATE = env('SENTRY_PROFILES_SAMPLE_RATE', '0.1')
SENTRY_ENVIRONMENT = env('SENTRY_ENVIRONMENT', 'development')
APP_VERSION = env('APP_VERSION', '1.0.0')

# Prometheus metrics
METRICS_API_KEY = env('METRICS_API_KEY', '')

# Initialize Sentry (only if DSN is set)
if SENTRY_DSN:
    from services.sentry import init_sentry
    init_sentry()
