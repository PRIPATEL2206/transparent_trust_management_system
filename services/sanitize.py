import re
from html import escape


DANGEROUS_TAGS = re.compile(
    r'<\s*/?\s*(script|iframe|object|embed|form|input|button|link|meta|style|svg|math|base)'
    r'[^>]*>',
    re.IGNORECASE | re.DOTALL
)
DANGEROUS_ATTRS = re.compile(
    r'\s(on\w+|style|srcdoc|formaction|action|background)\s*=\s*["\'][^"\']*["\']',
    re.IGNORECASE
)
JS_PROTOCOL = re.compile(
    r'(href|src|action)\s*=\s*["\']?\s*(javascript|data|vbscript)\s*:',
    re.IGNORECASE
)


def sanitize_text(text):
    """Remove dangerous HTML from user text input. Returns cleaned string."""
    if not text:
        return text

    cleaned = DANGEROUS_TAGS.sub('', text)
    cleaned = DANGEROUS_ATTRS.sub('', cleaned)
    cleaned = JS_PROTOCOL.sub('', cleaned)
    return cleaned


def escape_html(text):
    """Escape all HTML entities. Use when output must be plain text."""
    if not text:
        return text
    return escape(text)


def sanitize_filename(filename):
    """Sanitize a filename to prevent path traversal and injection."""
    if not filename:
        return 'unnamed'
    filename = filename.replace('\\', '/').split('/')[-1]
    filename = re.sub(r'[^\w\s\-.]', '', filename)
    filename = filename.strip('. ')
    return filename or 'unnamed'
