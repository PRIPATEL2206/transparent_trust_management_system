from django.core.cache import cache

from .services import NotificationService


def notifications_context(request):
    if request.path.startswith(('/static/', '/media/', '/health/', '/robots.txt')):
        return {}
    if request.user.is_authenticated:
        cache_key = f'unread_notif_count:{request.user.id}'
        count = cache.get(cache_key)
        if count is None:
            count = NotificationService.get_unread_count(request.user)
            cache.set(cache_key, count, 30)
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}
