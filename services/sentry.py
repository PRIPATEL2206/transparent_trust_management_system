"""
Sentry integration for error tracking and performance monitoring.

Configure via environment variables:
    SENTRY_DSN=https://key@sentry.io/project
    SENTRY_TRACES_SAMPLE_RATE=0.1
    SENTRY_PROFILES_SAMPLE_RATE=0.1
    SENTRY_ENVIRONMENT=production
"""
import logging
from django.conf import settings

logger = logging.getLogger('services')


def init_sentry():
    dsn = getattr(settings, 'SENTRY_DSN', '')
    if not dsn:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )

        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                DjangoIntegration(
                    transaction_style='url',
                    middleware_spans=True,
                ),
                sentry_logging,
            ],
            traces_sample_rate=float(getattr(settings, 'SENTRY_TRACES_SAMPLE_RATE', 0.1)),
            profiles_sample_rate=float(getattr(settings, 'SENTRY_PROFILES_SAMPLE_RATE', 0.1)),
            environment=getattr(settings, 'SENTRY_ENVIRONMENT', 'production'),
            release=getattr(settings, 'APP_VERSION', 'unknown'),
            send_default_pii=False,
            before_send=_before_send,
            traces_sampler=_traces_sampler,
        )
        logger.info("Sentry initialized successfully")
    except ImportError:
        logger.warning("sentry-sdk not installed — error tracking disabled")
    except Exception as e:
        logger.error(f"Sentry initialization failed: {e}")


def _before_send(event, hint):
    """Filter out noisy or sensitive events before sending to Sentry."""
    if 'exc_info' in hint:
        exc_type, exc_value, _ = hint['exc_info']
        exc_name = exc_type.__name__ if exc_type else ''

        # Don't report expected 404s, permission denials, rate limits
        ignored = ('Http404', 'PermissionDenied', 'DisallowedHost', 'SuspiciousOperation')
        if exc_name in ignored:
            return None

    # Strip sensitive headers
    if 'request' in event:
        headers = event['request'].get('headers', {})
        for key in ('Cookie', 'Authorization', 'X-CSRFToken'):
            if key in headers:
                headers[key] = '[filtered]'

    return event


def _traces_sampler(sampling_context):
    """Reduce sampling for health checks and static assets."""
    path = sampling_context.get('wsgi_environ', {}).get('PATH_INFO', '')

    if path.startswith('/health/') or path.startswith('/static/') or path.startswith('/media/'):
        return 0.0

    if path.startswith('/api/'):
        return 0.3

    return float(getattr(settings, 'SENTRY_TRACES_SAMPLE_RATE', 0.1))
