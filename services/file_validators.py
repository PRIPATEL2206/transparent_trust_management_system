import mimetypes
from django.core.exceptions import ValidationError


ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
ALLOWED_DOCUMENT_TYPES = {'application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
BLOCKED_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.msi', '.scr', '.pif', '.vbs', '.js',
    '.ws', '.wsf', '.sh', '.csh', '.bash', '.ps1', '.php', '.py', '.rb',
    '.pl', '.jar', '.html', '.htm', '.svg', '.xml', '.swf',
}


def validate_upload_image(file):
    _validate_file(file, ALLOWED_IMAGE_TYPES, max_mb=5)


def validate_upload_document(file):
    _validate_file(file, ALLOWED_DOCUMENT_TYPES, max_mb=10)


def _validate_file(file, allowed_types, max_mb=10):
    if not file:
        return

    ext = ''
    if hasattr(file, 'name') and file.name:
        ext = '.' + file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''

    if ext in BLOCKED_EXTENSIONS:
        raise ValidationError(f'File type "{ext}" is not allowed.')

    content_type = getattr(file, 'content_type', '')
    if content_type and content_type not in allowed_types:
        guessed, _ = mimetypes.guess_type(file.name or '')
        if guessed not in allowed_types:
            raise ValidationError(f'File type "{content_type}" is not permitted. Allowed: {", ".join(sorted(allowed_types))}')

    max_bytes = max_mb * 1024 * 1024
    if hasattr(file, 'size') and file.size > max_bytes:
        raise ValidationError(f'File exceeds maximum size of {max_mb}MB.')

    if hasattr(file, 'seek') and hasattr(file, 'read'):
        file.seek(0)
        header = file.read(8)
        file.seek(0)
        if header[:2] == b'MZ' or header[:4] == b'\x7fELF':
            raise ValidationError('Executable files are not allowed.')
