from .base import *  # noqa: F401,F403


DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
        'CONN_MAX_AGE': 0,
        'CONN_HEALTH_CHECKS': False,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'trust-mgmt-dev',
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Relax throttle for development
THROTTLE_MAX_REQUESTS = 1000
THROTTLE_WINDOW = 60

# Disable password age in dev
PASSWORD_MAX_AGE_DAYS = 0

# Logging uses verbose formatter in dev (set in base via DEBUG flag)
