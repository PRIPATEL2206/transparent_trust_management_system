from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_not_required
from django.core.cache import cache
from django.db import connection


@login_not_required
def home_view(request):
    context = {}
    if request.user.is_authenticated:
        from roles.services import RoleService
        role = RoleService.get_user_role(request.user)
        if role in ('admin', 'super_admin'):
            from django.core.cache import cache
            cache_key = 'home_admin_counts'
            counts = cache.get(cache_key)
            if counts is None:
                from donations.models import Donation
                from expenses.models import Expense
                from approval_engine.models import ApprovalRequest
                counts = {
                    'pending_donations': Donation.objects.filter(is_approved=False).count(),
                    'pending_expenses': Expense.objects.filter(status='pending').count(),
                    'pending_approvals': ApprovalRequest.objects.filter(status='pending').count(),
                }
                cache.set(cache_key, counts, 30)
            context.update(counts)
    return render(request, 'home/home.html', context)


@login_not_required
def health_check(request):
    from django.conf import settings as conf

    health_key = getattr(conf, 'HEALTH_CHECK_API_KEY', '')
    is_authenticated = False
    if health_key:
        provided_key = request.headers.get('X-Health-Key', '') or request.GET.get('key', '')
        is_authenticated = (provided_key == health_key)

    cached = cache.get('health_check_result')
    if cached is not None and not is_authenticated:
        return JsonResponse({'status': cached['status']}, status=200 if cached['status'] == 'healthy' else 503)

    checks = {}

    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = 'connected'
    except Exception:
        checks['database'] = 'unavailable'

    try:
        cache.set('_health_probe', '1', 5)
        checks['cache'] = 'connected' if cache.get('_health_probe') == '1' else 'unavailable'
    except Exception:
        checks['cache'] = 'unavailable'

    import shutil
    try:
        disk = shutil.disk_usage('/')
        free_mb = disk.free // (1024 * 1024)
        checks['disk_free_mb'] = free_mb
        checks['disk'] = 'ok' if free_mb > 100 else 'low'
    except Exception:
        checks['disk'] = 'unknown'

    all_ok = checks['database'] == 'connected' and checks.get('cache') == 'connected'
    status = 'healthy' if all_ok else 'degraded'
    code = 200 if checks['database'] == 'connected' else 503
    result = {'status': status, **checks}

    if all_ok:
        cache.set('health_check_result', result, 10)

    if is_authenticated:
        return JsonResponse(result, status=code)
    return JsonResponse({'status': status}, status=code)


@login_not_required
def liveness_probe(request):
    """Lightweight liveness probe — confirms the process is running and can serve HTTP."""
    return JsonResponse({'status': 'alive'}, status=200)


@login_not_required
def readiness_probe(request):
    """Readiness probe — checks if app can handle traffic (DB + cache accessible)."""
    checks = {}

    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = True
    except Exception:
        checks['database'] = False

    try:
        cache.set('_readiness_probe', '1', 5)
        checks['cache'] = cache.get('_readiness_probe') == '1'
    except Exception:
        checks['cache'] = False

    ready = all(checks.values())
    return JsonResponse(
        {'ready': ready, 'checks': checks},
        status=200 if ready else 503
    )



@login_not_required
def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /auth/',
        'Disallow: /config/',
        'Disallow: /dashboard/',
        'Disallow: /chat/',
        '',
        f'Sitemap: {request.build_absolute_uri("/sitemap.xml")}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


@login_not_required
def sitemap_xml(request):
    from config_app.services import ConfigService
    config = ConfigService.get_config()

    base = request.build_absolute_uri('/').rstrip('/')
    urls = [
        ('/', 'daily', '1.0'),
        ('/transparency/', 'daily', '0.9'),
        ('/donation/', 'weekly', '0.8'),
        ('/products/', 'weekly', '0.8'),
        ('/notices/', 'daily', '0.7'),
    ]

    xml_entries = []
    for path, freq, priority in urls:
        xml_entries.append(
            f'  <url>\n'
            f'    <loc>{base}{path}</loc>\n'
            f'    <changefreq>{freq}</changefreq>\n'
            f'    <priority>{priority}</priority>\n'
            f'  </url>'
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(xml_entries) + '\n'
        '</urlset>'
    )
    return HttpResponse(xml, content_type='application/xml')


@login_not_required
def security_txt(request):
    from config_app.services import ConfigService
    config = ConfigService.get_config()
    contact_email = getattr(config, 'contact_email', '') if config else ''
    if not contact_email:
        contact_email = 'admin@trustmanagement.org'

    content = (
        f"Contact: mailto:{contact_email}\n"
        f"Preferred-Languages: en\n"
        f"Canonical: {request.build_absolute_uri('/.well-known/security.txt')}\n"
        f"Policy: {request.build_absolute_uri('/security-policy/')}\n"
    )
    return HttpResponse(content, content_type='text/plain')
