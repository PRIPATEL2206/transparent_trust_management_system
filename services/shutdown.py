"""
Graceful shutdown signal handlers.

Ensures in-flight requests complete and resources clean up properly
when the process receives SIGTERM (Docker stop, Kubernetes pod termination).
"""

import atexit
import logging
import signal
import threading

logger = logging.getLogger('services')

_shutdown_event = threading.Event()


def is_shutting_down():
    return _shutdown_event.is_set()


def _handle_sigterm(signum, frame):
    logger.info('[SHUTDOWN] SIGTERM received — initiating graceful shutdown.')
    _shutdown_event.set()


def _cleanup():
    logger.info('[SHUTDOWN] Running cleanup handlers.')
    try:
        from django.db import connections
        for conn in connections.all():
            conn.close()
    except Exception:
        pass

    try:
        from django.core.cache import cache
        cache.close()
    except Exception:
        pass

    logger.info('[SHUTDOWN] Cleanup complete.')


def register_shutdown_handlers():
    signal.signal(signal.SIGTERM, _handle_sigterm)
    atexit.register(_cleanup)
    logger.debug('[SHUTDOWN] Graceful shutdown handlers registered.')
