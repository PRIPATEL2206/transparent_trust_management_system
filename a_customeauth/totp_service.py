import base64
import hashlib
import hmac
import secrets
import struct
import time
import logging
from urllib.parse import quote

from django.conf import settings
from django.utils import timezone

from .models import TOTPDevice

logger = logging.getLogger('services')

TOTP_DIGITS = 6
TOTP_PERIOD = 30
TOTP_WINDOW = 1  # allow 1 period before/after


class TOTPService:

    @staticmethod
    def generate_secret():
        return base64.b32encode(secrets.token_bytes(20)).decode('ascii')

    @staticmethod
    def get_totp_code(secret, time_step=None):
        if time_step is None:
            time_step = int(time.time()) // TOTP_PERIOD
        secret_bytes = base64.b32decode(secret.upper())
        msg = struct.pack('>Q', time_step)
        h = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        truncated = struct.unpack('>I', h[offset:offset + 4])[0] & 0x7FFFFFFF
        code = truncated % (10 ** TOTP_DIGITS)
        return str(code).zfill(TOTP_DIGITS)

    @staticmethod
    def verify_code(secret, code, window=TOTP_WINDOW):
        code = code.strip().replace(' ', '')
        if len(code) != TOTP_DIGITS:
            return False
        current_step = int(time.time()) // TOTP_PERIOD
        for offset in range(-window, window + 1):
            expected = TOTPService.get_totp_code(secret, current_step + offset)
            if hmac.compare_digest(code, expected):
                return True
        return False

    @staticmethod
    def setup_2fa(user):
        secret = TOTPService.generate_secret()
        device, created = TOTPDevice.objects.get_or_create(
            user=user,
            defaults={'secret': secret, 'is_active': False, 'is_confirmed': False}
        )
        if not created and not device.is_confirmed:
            device.secret = secret
            device.save(update_fields=['secret'])
        return device

    @staticmethod
    def confirm_2fa(user, code):
        try:
            device = user.totp_device
        except TOTPDevice.DoesNotExist:
            return None, 'no_device'

        if device.is_confirmed:
            return None, 'already_confirmed'

        if not TOTPService.verify_code(device.secret, code):
            return None, 'invalid_code'

        device.is_confirmed = True
        device.is_active = True
        device.save(update_fields=['is_confirmed', 'is_active'])
        backup_codes = device.generate_backup_codes()
        return backup_codes, 'success'

    @staticmethod
    def verify_login(user, code):
        try:
            device = user.totp_device
        except TOTPDevice.DoesNotExist:
            return False

        if not device.is_active:
            return False

        if TOTPService.verify_code(device.secret, code):
            device.last_used_at = timezone.now()
            device.save(update_fields=['last_used_at'])
            return True

        if device.verify_backup_code(code):
            device.last_used_at = timezone.now()
            device.save(update_fields=['last_used_at'])
            logger.warning(f"Backup code used for user {user.username}")
            return True

        return False

    @staticmethod
    def disable_2fa(user):
        try:
            device = user.totp_device
            device.is_active = False
            device.is_confirmed = False
            device.backup_codes = ''
            device.save()
            return True
        except TOTPDevice.DoesNotExist:
            return False

    @staticmethod
    def is_2fa_enabled(user):
        try:
            return user.totp_device.is_active and user.totp_device.is_confirmed
        except TOTPDevice.DoesNotExist:
            return False

    @staticmethod
    def requires_2fa(user):
        from roles.services import RoleService
        role = RoleService.get_user_role(user)
        return role in ('admin', 'super_admin')

    @staticmethod
    def get_provisioning_uri(user, secret):
        issuer = getattr(settings, 'TOTP_ISSUER', 'TrustManagement')
        label = f"{issuer}:{user.email or user.username}"
        params = f"secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_PERIOD}"
        return f"otpauth://totp/{quote(label)}?{params}"

    @staticmethod
    def generate_qr_data_url(uri):
        try:
            import qrcode
            import io
            import base64 as b64
            qr = qrcode.QRCode(version=1, box_size=6, border=2)
            qr.add_data(uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            encoded = b64.b64encode(buffer.getvalue()).decode('ascii')
            return f"data:image/png;base64,{encoded}"
        except ImportError:
            return None
