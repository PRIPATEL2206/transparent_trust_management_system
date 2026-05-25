"""
Audit logging for security-sensitive operations.

Writes structured audit events to a dedicated log file and the 'audit' logger.
Each event includes who, what, when, from where, and outcome.
"""

import logging
from datetime import datetime, timezone

from services.logging import get_current_request

logger = logging.getLogger('audit')


def _build_event(action, user=None, target=None, outcome='success', detail=''):
    request = get_current_request()

    event = {
        'action': action,
        'outcome': outcome,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }

    if user:
        event['actor'] = user.username if hasattr(user, 'username') else str(user)
    elif request and hasattr(request, 'user') and request.user.is_authenticated:
        event['actor'] = request.user.username
    else:
        event['actor'] = 'anonymous'

    if target:
        event['target'] = str(target)

    if detail:
        event['detail'] = detail

    if request:
        event['ip'] = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '-')
        )
        event['request_id'] = getattr(request, 'request_id', '-')
        event['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:200]

    return event


def log_auth_event(action, user=None, outcome='success', detail=''):
    event = _build_event(action, user=user, outcome=outcome, detail=detail)
    level = logging.WARNING if outcome == 'failure' else logging.INFO
    logger.log(level, '%s: %s', action, event)


def log_login_success(user):
    log_auth_event('login', user=user, outcome='success')


def log_login_failure(username, reason='invalid_credentials'):
    log_auth_event('login_attempt', detail=f'username={username} reason={reason}', outcome='failure')


def log_logout(user):
    log_auth_event('logout', user=user)


def log_session_expired(user, reason='idle'):
    log_auth_event('session_expired', user=user, detail=f'reason={reason}')


def log_2fa_event(action, user, outcome='success'):
    log_auth_event(f'2fa_{action}', user=user, outcome=outcome)


def log_role_change(user, target_user, old_role, new_role):
    event = _build_event(
        'role_change', user=user, target=target_user.username,
        detail=f'{old_role} -> {new_role}'
    )
    logger.info('role_change: %s', event)


def log_approval_action(action, user, approval_request):
    event = _build_event(
        f'approval_{action}', user=user,
        target=f'{approval_request.content_type.model}:{approval_request.object_id}',
    )
    logger.info('approval_%s: %s', action, event)


def log_password_change(user, forced=False):
    detail = 'forced=True' if forced else ''
    log_auth_event('password_change', user=user, detail=detail)


def log_data_export(user, export_type, record_count):
    event = _build_event(
        'data_export', user=user,
        detail=f'type={export_type} records={record_count}'
    )
    logger.info('data_export: %s', event)


def log_admin_action(user, action, target='', detail=''):
    event = _build_event(action, user=user, target=target, detail=detail)
    logger.info('admin_action: %s', event)
