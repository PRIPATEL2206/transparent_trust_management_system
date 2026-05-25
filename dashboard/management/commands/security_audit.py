import os

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Audit the security configuration and report issues'

    def add_arguments(self, parser):
        parser.add_argument('--strict', action='store_true', help='Treat warnings as errors (non-zero exit)')

    def handle(self, *args, **options):
        self.stdout.write('Security Configuration Audit\n' + '=' * 40 + '\n')
        findings = {'error': [], 'warning': [], 'pass': []}

        self._check_secret_key(findings)
        self._check_debug(findings)
        self._check_allowed_hosts(findings)
        self._check_session_security(findings)
        self._check_csrf_security(findings)
        self._check_middleware(findings)
        self._check_password_validators(findings)
        self._check_https_settings(findings)
        self._check_database(findings)
        self._check_admin_url(findings)
        self._check_file_permissions(findings)
        self._check_environment_variables(findings)

        self.stdout.write('\n' + '=' * 40)
        self.stdout.write(self.style.SUCCESS(f'  PASS: {len(findings["pass"])}'))
        self.stdout.write(self.style.WARNING(f'  WARN: {len(findings["warning"])}'))
        self.stdout.write(self.style.ERROR(f'  FAIL: {len(findings["error"])}'))

        if options['strict'] and (findings['error'] or findings['warning']):
            raise SystemExit(1)
        elif findings['error']:
            raise SystemExit(1)

    def _report(self, findings, level, msg):
        findings[level].append(msg)
        if level == 'pass':
            self.stdout.write(self.style.SUCCESS(f'  [PASS] {msg}'))
        elif level == 'warning':
            self.stdout.write(self.style.WARNING(f'  [WARN] {msg}'))
        else:
            self.stdout.write(self.style.ERROR(f'  [FAIL] {msg}'))

    def _check_secret_key(self, findings):
        self.stdout.write('\n[Secret Key]')
        if 'insecure' in settings.SECRET_KEY or settings.SECRET_KEY == 'changeme':
            self._report(findings, 'error', 'Using default/insecure SECRET_KEY')
        elif len(settings.SECRET_KEY) < 50:
            self._report(findings, 'warning', f'SECRET_KEY is short ({len(settings.SECRET_KEY)} chars, recommend 50+)')
        else:
            self._report(findings, 'pass', 'SECRET_KEY is properly configured')

    def _check_debug(self, findings):
        self.stdout.write('\n[Debug Mode]')
        if settings.DEBUG:
            self._report(findings, 'warning', 'DEBUG=True (must be False in production)')
        else:
            self._report(findings, 'pass', 'DEBUG is off')

    def _check_allowed_hosts(self, findings):
        self.stdout.write('\n[Allowed Hosts]')
        hosts = settings.ALLOWED_HOSTS
        if '*' in hosts:
            self._report(findings, 'error', 'ALLOWED_HOSTS contains wildcard *')
        elif not hosts:
            self._report(findings, 'error', 'ALLOWED_HOSTS is empty')
        else:
            self._report(findings, 'pass', f'ALLOWED_HOSTS: {", ".join(hosts)}')

    def _check_session_security(self, findings):
        self.stdout.write('\n[Session Security]')
        if settings.SESSION_COOKIE_HTTPONLY:
            self._report(findings, 'pass', 'SESSION_COOKIE_HTTPONLY is True')
        else:
            self._report(findings, 'error', 'SESSION_COOKIE_HTTPONLY is False')

        if settings.SESSION_COOKIE_SAMESITE in ('Lax', 'Strict'):
            self._report(findings, 'pass', f'SESSION_COOKIE_SAMESITE={settings.SESSION_COOKIE_SAMESITE}')
        else:
            self._report(findings, 'warning', f'SESSION_COOKIE_SAMESITE={settings.SESSION_COOKIE_SAMESITE}')

        idle_timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', None)
        if idle_timeout and idle_timeout <= 1800:
            self._report(findings, 'pass', f'Session idle timeout: {idle_timeout}s')
        else:
            self._report(findings, 'warning', 'No session idle timeout or >30min')

        max_sessions = getattr(settings, 'MAX_SESSIONS_PER_USER', None)
        if max_sessions:
            self._report(findings, 'pass', f'Max sessions per user: {max_sessions}')
        else:
            self._report(findings, 'warning', 'No concurrent session limit')

    def _check_csrf_security(self, findings):
        self.stdout.write('\n[CSRF Protection]')
        if settings.CSRF_COOKIE_HTTPONLY:
            self._report(findings, 'pass', 'CSRF_COOKIE_HTTPONLY is True')
        else:
            self._report(findings, 'warning', 'CSRF_COOKIE_HTTPONLY is False')

        if settings.CSRF_COOKIE_SAMESITE in ('Lax', 'Strict'):
            self._report(findings, 'pass', f'CSRF_COOKIE_SAMESITE={settings.CSRF_COOKIE_SAMESITE}')
        else:
            self._report(findings, 'warning', f'CSRF_COOKIE_SAMESITE={settings.CSRF_COOKIE_SAMESITE}')

    def _check_middleware(self, findings):
        self.stdout.write('\n[Middleware Stack]')
        required = [
            'SecurityMiddleware',
            'SessionMiddleware',
            'CsrfViewMiddleware',
            'SecurityHeadersMiddleware',
            'GlobalThrottleMiddleware',
        ]
        mw_str = ' '.join(settings.MIDDLEWARE)
        for mw in required:
            if mw in mw_str:
                self._report(findings, 'pass', f'{mw} is active')
            else:
                self._report(findings, 'error', f'{mw} is missing from MIDDLEWARE')

    def _check_password_validators(self, findings):
        self.stdout.write('\n[Password Policy]')
        validators = settings.AUTH_PASSWORD_VALIDATORS
        names = [v['NAME'].split('.')[-1] for v in validators]
        if 'ComplexityValidator' in names:
            self._report(findings, 'pass', 'ComplexityValidator active')
        else:
            self._report(findings, 'warning', 'No ComplexityValidator — weak passwords possible')

        if 'BreachedPasswordValidator' in names:
            self._report(findings, 'pass', 'BreachedPasswordValidator active')
        else:
            self._report(findings, 'warning', 'No BreachedPasswordValidator')

        min_len_validator = next((v for v in validators if 'MinimumLength' in v['NAME']), None)
        if min_len_validator:
            min_len = min_len_validator.get('OPTIONS', {}).get('min_length', 8)
            if min_len >= 10:
                self._report(findings, 'pass', f'Minimum password length: {min_len}')
            else:
                self._report(findings, 'warning', f'Minimum password length too low: {min_len}')

    def _check_https_settings(self, findings):
        self.stdout.write('\n[HTTPS/TLS]')
        if not settings.DEBUG:
            if getattr(settings, 'SECURE_SSL_REDIRECT', False):
                self._report(findings, 'pass', 'SECURE_SSL_REDIRECT is True')
            else:
                self._report(findings, 'warning', 'SECURE_SSL_REDIRECT is False')

            if getattr(settings, 'SECURE_HSTS_SECONDS', 0) >= 31536000:
                self._report(findings, 'pass', 'HSTS enabled (1+ year)')
            else:
                self._report(findings, 'warning', 'HSTS not configured or too short')

            if getattr(settings, 'SESSION_COOKIE_SECURE', False):
                self._report(findings, 'pass', 'SESSION_COOKIE_SECURE is True')
            else:
                self._report(findings, 'error', 'SESSION_COOKIE_SECURE is False in production')
        else:
            self._report(findings, 'pass', 'Skipping HTTPS checks (DEBUG=True)')

    def _check_database(self, findings):
        self.stdout.write('\n[Database]')
        engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite' in engine and not settings.DEBUG:
            self._report(findings, 'warning', 'SQLite in non-debug mode — use PostgreSQL for production')
        else:
            self._report(findings, 'pass', f'Database engine: {engine.split(".")[-1]}')

    def _check_admin_url(self, findings):
        self.stdout.write('\n[Admin Panel]')
        from django.urls import get_resolver
        url_patterns = [str(p.pattern) for p in get_resolver().url_patterns]
        if 'admin/' in url_patterns:
            self._report(findings, 'warning', 'Django admin accessible at default /admin/ path')
        else:
            self._report(findings, 'pass', 'Admin URL is obfuscated (not at /admin/)')

    def _check_file_permissions(self, findings):
        self.stdout.write('\n[File System]')
        env_file = settings.BASE_DIR / '.env'
        if env_file.exists():
            self._report(findings, 'pass', '.env file exists')
        else:
            self._report(findings, 'warning', 'No .env file found (using defaults or OS env)')

        db_file = settings.BASE_DIR / 'db.sqlite3'
        if db_file.exists() and not settings.DEBUG:
            self._report(findings, 'warning', 'SQLite DB file present in non-debug deployment')

    def _check_environment_variables(self, findings):
        self.stdout.write('\n[Environment]')
        critical_vars = ['DJANGO_SECRET_KEY']
        for var in critical_vars:
            if os.environ.get(var):
                self._report(findings, 'pass', f'{var} set via environment')
            else:
                self._report(findings, 'warning', f'{var} not in environment (using fallback)')
