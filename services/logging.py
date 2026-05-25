import json
import logging
import re
import traceback
import threading
from datetime import datetime, timezone


SENSITIVE_PATTERNS = re.compile(
    r'(password|passwd|secret|token|api_key|apikey|auth|credential|ssn|credit_card)',
    re.IGNORECASE
)
MASK = '***FILTERED***'

_request_local = threading.local()


def get_current_request():
    return getattr(_request_local, 'request', None)


def set_current_request(request):
    _request_local.request = request


def clear_current_request():
    _request_local.request = None


class RequestContextFilter(logging.Filter):
    """Injects request_id, user, and IP into every log record automatically."""

    def filter(self, record):
        request = get_current_request()
        if request:
            record.request_id = getattr(request, 'request_id', '-')
            user = getattr(request, 'user', None)
            record.user = user.username if user and hasattr(user, 'username') and getattr(user, 'is_authenticated', False) else 'anonymous'
            record.ip = (
                request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                or request.META.get('REMOTE_ADDR', '-')
            )
        else:
            record.request_id = getattr(record, 'request_id', '-')
            record.user = getattr(record, 'user', '-')
            record.ip = getattr(record, 'ip', '-')
        return True


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production log aggregation (ELK, CloudWatch, Datadog)."""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': self._mask_sensitive(record.getMessage()),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id

        if hasattr(record, 'user'):
            log_entry['user'] = record.user

        if hasattr(record, 'ip'):
            log_entry['ip'] = record.ip

        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info),
            }

        extra_keys = set(record.__dict__.keys()) - {
            'name', 'msg', 'args', 'created', 'relativeCreated', 'thread',
            'threadName', 'msecs', 'filename', 'funcName', 'levelno',
            'lineno', 'module', 'exc_info', 'exc_text', 'stack_info',
            'pathname', 'processName', 'process', 'message', 'levelname',
            'taskName', 'request_id', 'user', 'ip',
        }
        for key in extra_keys:
            val = getattr(record, key, None)
            if val is not None and isinstance(val, (str, int, float, bool)):
                if SENSITIVE_PATTERNS.search(key):
                    log_entry[key] = MASK
                else:
                    log_entry[key] = val

        return json.dumps(log_entry, default=str)

    def _mask_sensitive(self, message):
        """Mask values that look like they follow sensitive keys in log messages."""
        return re.sub(
            r'(password|token|secret|api_key|credential)[=:]\s*\S+',
            r'\1=' + MASK,
            message,
            flags=re.IGNORECASE
        )


class SensitiveFilter(logging.Filter):
    """Filter that redacts sensitive data patterns from log records."""

    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = re.sub(
                r'(password|token|secret|api_key|credential)[=:]\s*\S+',
                r'\1=' + MASK,
                record.msg,
                flags=re.IGNORECASE
            )
        return True
