"""
Lightweight Prometheus metrics — no external dependency.

Exposes /metrics/ endpoint in Prometheus text exposition format.
Collects: request count, latency histogram, active requests, error count,
plus application-specific business metrics.
"""
import time
import threading
from collections import defaultdict
from django.http import HttpResponse
from django.contrib.auth.decorators import login_not_required


_lock = threading.Lock()

# Core HTTP metrics
_request_count = defaultdict(int)       # {method_status_path: count}
_request_latency_sum = defaultdict(float)
_request_latency_count = defaultdict(int)
_error_count = defaultdict(int)         # {status_code: count}
_active_requests = 0

# Business metrics
_business_counters = defaultdict(int)
_business_gauges = {}


class MetricsMiddleware:
    """Collects per-request metrics for Prometheus exposition."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _active_requests

        if request.path == '/metrics/':
            return self.get_response(request)

        with _lock:
            _active_requests += 1

        start = time.time()
        try:
            response = self.get_response(request)
        except Exception:
            with _lock:
                _active_requests -= 1
                _error_count['500'] += 1
            raise

        duration = time.time() - start
        status = str(response.status_code)
        method = request.method
        path = _normalize_path(request.path)

        with _lock:
            _active_requests -= 1
            key = f'{method}_{status}_{path}'
            _request_count[key] += 1
            _request_latency_sum[key] += duration
            _request_latency_count[key] += 1
            if response.status_code >= 400:
                _error_count[status] += 1

        return response


def increment_counter(name, value=1):
    """Increment a business metric counter."""
    with _lock:
        _business_counters[name] += value


def set_gauge(name, value):
    """Set a business metric gauge to a specific value."""
    with _lock:
        _business_gauges[name] = value


def _normalize_path(path):
    """Collapse path parameters to reduce cardinality."""
    parts = path.strip('/').split('/')
    normalized = []
    for part in parts[:3]:
        if part.isdigit() or len(part) > 30:
            normalized.append(':id')
        else:
            normalized.append(part)
    return '/' + '/'.join(normalized) if normalized else '/'


@login_not_required
def metrics_view(request):
    """Prometheus text exposition format endpoint."""
    from django.conf import settings
    api_key = getattr(settings, 'METRICS_API_KEY', '')
    if api_key and request.META.get('HTTP_AUTHORIZATION') != f'Bearer {api_key}':
        return HttpResponse('Unauthorized', status=401)

    lines = []

    # HTTP request metrics
    lines.append('# HELP http_requests_total Total HTTP requests')
    lines.append('# TYPE http_requests_total counter')
    with _lock:
        for key, count in sorted(_request_count.items()):
            parts = key.split('_', 2)
            if len(parts) == 3:
                method, status, path = parts
                lines.append(f'http_requests_total{{method="{method}",status="{status}",path="{path}"}} {count}')

    lines.append('')
    lines.append('# HELP http_request_duration_seconds HTTP request latency')
    lines.append('# TYPE http_request_duration_seconds summary')
    with _lock:
        for key in sorted(_request_latency_sum.keys()):
            parts = key.split('_', 2)
            if len(parts) == 3:
                method, status, path = parts
                total = _request_latency_sum[key]
                count = _request_latency_count[key]
                lines.append(f'http_request_duration_seconds_sum{{method="{method}",status="{status}",path="{path}"}} {total:.4f}')
                lines.append(f'http_request_duration_seconds_count{{method="{method}",status="{status}",path="{path}"}} {count}')

    lines.append('')
    lines.append('# HELP http_requests_active Current active requests')
    lines.append('# TYPE http_requests_active gauge')
    lines.append(f'http_requests_active {_active_requests}')

    lines.append('')
    lines.append('# HELP http_errors_total HTTP error responses')
    lines.append('# TYPE http_errors_total counter')
    with _lock:
        for status, count in sorted(_error_count.items()):
            lines.append(f'http_errors_total{{status="{status}"}} {count}')

    # Business metrics
    if _business_counters:
        lines.append('')
        lines.append('# HELP app_business_total Application business metrics')
        lines.append('# TYPE app_business_total counter')
        with _lock:
            for name, value in sorted(_business_counters.items()):
                lines.append(f'app_business_total{{metric="{name}"}} {value}')

    if _business_gauges:
        lines.append('')
        lines.append('# HELP app_business_gauge Application business gauges')
        lines.append('# TYPE app_business_gauge gauge')
        with _lock:
            for name, value in sorted(_business_gauges.items()):
                lines.append(f'app_business_gauge{{metric="{name}"}} {value}')

    lines.append('')
    body = '\n'.join(lines)
    return HttpResponse(body, content_type='text/plain; version=0.0.4; charset=utf-8')
