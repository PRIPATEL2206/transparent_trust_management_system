import hashlib
import logging
import re

import urllib.request
from django.core.exceptions import ValidationError

logger = logging.getLogger('services')


class ComplexityValidator:
    """Requires at least one uppercase, one lowercase, one digit, and one special character."""

    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                "Password must contain at least one uppercase letter.",
                code='password_no_upper',
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                "Password must contain at least one lowercase letter.",
                code='password_no_lower',
            )
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                "Password must contain at least one digit.",
                code='password_no_digit',
            )
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError(
                "Password must contain at least one special character.",
                code='password_no_special',
            )

    def get_help_text(self):
        return "Your password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character."


class BreachedPasswordValidator:
    """Checks password against HaveIBeenPwned using k-anonymity (only sends first 5 chars of SHA-1)."""

    def validate(self, password, user=None):
        sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]

        try:
            url = f'https://api.pwnedpasswords.com/range/{prefix}'
            req = urllib.request.Request(url, headers={'User-Agent': 'TrustManagement-PasswordCheck'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                body = resp.read().decode('utf-8')
            for line in body.splitlines():
                hash_suffix, count = line.split(':')
                if hash_suffix.strip() == suffix:
                    raise ValidationError(
                        "This password has appeared in a data breach and is not safe to use. Please choose a different password.",
                        code='password_breached',
                    )
        except (urllib.error.URLError, OSError, TimeoutError):
            logger.debug('HaveIBeenPwned API unreachable, skipping breach check')

    def get_help_text(self):
        return "Your password must not appear in known data breaches."
