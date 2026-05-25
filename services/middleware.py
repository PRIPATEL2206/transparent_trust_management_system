import time
import uuid
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from .exceptions import ServiceError, PermissionDeniedError, NotFoundError

logger = logging.getLogger('services')


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .logging import set_current_request, clear_current_request

        request_id = request.META.get('HTTP_X_REQUEST_ID', str(uuid.uuid4())[:8])
        request.request_id = request_id
        set_current_request(request)
        try:
            response = self.get_response(request)
            response['X-Request-ID'] = request_id
            return response
        finally:
            clear_current_request()


class RequestBodySizeMiddleware:
    """Rejects requests with Content-Length exceeding the configured limit before body is read."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)

    def __call__(self, request):
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                if int(content_length) > self.max_size:
                    return HttpResponse(
                        '<h1>413 Request Entity Too Large</h1>',
                        status=413, content_type='text/html'
                    )
            except (ValueError, TypeError):
                pass
        return self.get_response(request)


class ServiceErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDeniedError):
            messages.error(request, exception.message)
            return redirect('home')
        if isinstance(exception, NotFoundError):
            messages.error(request, exception.message)
            return redirect('home')
        if isinstance(exception, ServiceError):
            messages.error(request, exception.message)
            referer = request.META.get('HTTP_REFERER', '/')
            if not url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                referer = '/'
            return redirect(referer)
        return None


class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration_ms = (time.time() - start) * 1000

        if duration_ms > 500:
            logger.warning(
                'Slow request: %s %s took %.0fms [%s]',
                request.method, request.path, duration_ms,
                getattr(request, 'request_id', '-')
            )

        response['X-Request-Duration-Ms'] = f'{duration_ms:.0f}'
        return response


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import secrets
        nonce = secrets.token_urlsafe(16)
        request.csp_nonce = nonce

        response = self.get_response(request)
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), payment=(), '
            'usb=(), magnetometer=(), gyroscope=(), accelerometer=()'
        )
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        if response.get('Content-Disposition', '').startswith('attachment'):
            response['X-Download-Options'] = 'noopen'
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = (
                f"default-src 'self'; "
                f"script-src 'self' 'nonce-{nonce}'; "
                f"style-src 'self' 'unsafe-inline'; "
                f"img-src 'self' data:; "
                f"font-src 'self'; "
                f"connect-src 'self' ws: wss:; "
                f"frame-ancestors 'none'"
            )
        return response


class IdleSessionTimeoutMiddleware:
    """Logs out users inactive for longer than SESSION_IDLE_TIMEOUT seconds.
    Also enforces a hard session lifetime (SESSION_MAX_AGE) that cannot be extended.
    Includes session fingerprinting: binds session to user-agent hash at login."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 1800)
        self.max_age = getattr(settings, 'SESSION_MAX_AGE', 86400)

    def __call__(self, request):
        if request.user.is_authenticated:
            now = time.time()

            session_start = request.session.get('_session_start')
            if session_start is None:
                request.session['_session_start'] = now
            elif (now - session_start) > self.max_age:
                from .audit import log_session_expired
                log_session_expired(request.user, reason='max_age')
                logout(request)
                messages.info(request, "Your session has reached its maximum duration. Please log in again.")
                return redirect('auth_login')

            last_activity = request.session.get('_last_activity')
            if last_activity and (now - last_activity) > self.timeout:
                from .audit import log_session_expired
                log_session_expired(request.user, reason='idle')
                logout(request)
                messages.info(request, "Your session expired due to inactivity. Please log in again.")
                return redirect('auth_login')
            request.session['_last_activity'] = now

            ua_hash = self._hash_ua(request)
            stored_hash = request.session.get('_ua_fingerprint')
            if stored_hash is None:
                request.session['_ua_fingerprint'] = ua_hash
            elif stored_hash != ua_hash:
                logger.warning(
                    'Session fingerprint mismatch: user=%s [%s]',
                    request.user.username, getattr(request, 'request_id', '-')
                )
                from .audit import log_session_expired
                log_session_expired(request.user, reason='fingerprint_mismatch')
                logout(request)
                messages.warning(request, "Session invalidated due to browser change. Please log in again.")
                return redirect('auth_login')

        response = self.get_response(request)
        return response

    @staticmethod
    def _hash_ua(request):
        import hashlib
        ua = request.META.get('HTTP_USER_AGENT', '')
        return hashlib.sha256(ua.encode()).hexdigest()[:16]


class AdminIPPinMiddleware:
    """Pins admin sessions to the IP used at login. IP change forces re-auth."""

    PINNED_ROLES = ('admin', 'super_admin')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            pinned_ip = request.session.get('_pinned_ip')
            current_ip = self._get_ip(request)

            if pinned_ip is None:
                from roles.services import RoleService
                role = RoleService.get_user_role(request.user)
                if role in self.PINNED_ROLES:
                    request.session['_pinned_ip'] = current_ip
            elif pinned_ip != current_ip:
                logger.warning(
                    'Admin session IP mismatch: user=%s pinned=%s current=%s [%s]',
                    request.user.username, pinned_ip, current_ip,
                    getattr(request, 'request_id', '-')
                )
                logout(request)
                messages.warning(request, "Session invalidated due to IP address change. Please log in again.")
                return redirect('auth_login')

        return self.get_response(request)

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class GlobalThrottleMiddleware:
    """Limits requests per IP to prevent abuse. Skips health check endpoints."""

    EXEMPT_PATHS = ('/health/', '/health/live/', '/health/ready/', '/metrics/')

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_requests = getattr(settings, 'THROTTLE_MAX_REQUESTS', 100)
        self.window = getattr(settings, 'THROTTLE_WINDOW', 60)

    def __call__(self, request):
        if request.path in self.EXEMPT_PATHS:
            return self.get_response(request)

        ip = self._get_ip(request)
        cache_key = f'throttle:{ip}'
        requests = cache.get(cache_key, 0)

        if requests >= self.max_requests:
            logger.warning('Throttled IP %s (%d requests in %ds)', ip, requests, self.window)
            return HttpResponse(
                '<h1>429 Too Many Requests</h1><p>Please slow down.</p>',
                status=429, content_type='text/html'
            )

        cache.set(cache_key, requests + 1, self.window)
        response = self.get_response(request)
        response['X-RateLimit-Limit'] = str(self.max_requests)
        response['X-RateLimit-Remaining'] = str(max(0, self.max_requests - requests - 1))
        return response

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class OriginCheckMiddleware:
    """Validates Origin/Referer header on state-changing requests as defense-in-depth alongside CSRF."""

    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS', 'TRACE')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in self.SAFE_METHODS:
            origin = request.META.get('HTTP_ORIGIN', '')
            referer = request.META.get('HTTP_REFERER', '')
            source = origin or referer

            if source:
                from urllib.parse import urlparse
                parsed = urlparse(source)
                allowed_host = request.get_host().split(':')[0]
                source_host = parsed.hostname or ''
                if source_host and source_host != allowed_host:
                    logger.warning(
                        'Origin mismatch: %s %s from %s (expected %s) [%s]',
                        request.method, request.path, source_host, allowed_host,
                        getattr(request, 'request_id', '-')
                    )

        return self.get_response(request)


class MediaContentTypeMiddleware:
    """Forces safe Content-Disposition and Content-Type on media file responses."""

    SAFE_CONTENT_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf',
    }

    def __init__(self, get_response):
        self.get_response = get_response
        self.media_url = getattr(settings, 'MEDIA_URL', '/media/')

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith(self.media_url):
            content_type = response.get('Content-Type', '').split(';')[0].strip()
            if content_type not in self.SAFE_CONTENT_TYPES:
                response['Content-Type'] = 'application/octet-stream'
                response['Content-Disposition'] = f'attachment; filename="{request.path.split("/")[-1]}"'
            response['X-Content-Type-Options'] = 'nosniff'

        return response


class PasswordAgeMiddleware:
    """Forces password change if the password is older than PASSWORD_MAX_AGE_DAYS."""

    EXEMPT_PATHS = ('/auth/settings', '/auth/logout', '/auth/2fa/', '/health/', '/static/', '/media/')

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_age_days = getattr(settings, 'PASSWORD_MAX_AGE_DAYS', 90)

    def __call__(self, request):
        if self.max_age_days <= 0:
            return self.get_response(request)

        if request.user.is_authenticated and not any(request.path.startswith(p) for p in self.EXEMPT_PATHS):
            from datetime import timedelta
            from django.utils import timezone

            profile = getattr(request.user, 'profile', None)
            if profile:
                changed_at = profile.password_changed_at
                if changed_at is None:
                    changed_at = request.user.date_joined

                age = timezone.now() - changed_at
                if age > timedelta(days=self.max_age_days):
                    messages.warning(request, "Your password has expired. Please change it to continue.")
                    return redirect('auth_settings')

        return self.get_response(request)
