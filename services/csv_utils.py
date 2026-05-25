import csv
from django.http import HttpResponse

FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def sanitize_csv_value(value):
    """Prevent CSV formula injection by prefixing dangerous values with a single quote."""
    s = str(value) if value is not None else ''
    if s and s[0] in FORMULA_PREFIXES:
        return "'" + s
    return s


def make_csv_response(filename, headers, rows):
    """Create a safe CSV HttpResponse with formula injection protection."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    _set_download_headers(response)
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([sanitize_csv_value(cell) for cell in row])
    return response


def make_file_response(content, filename, content_type):
    """Create a secure file download response with all safety headers."""
    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    _set_download_headers(response)
    return response


def _set_download_headers(response):
    """Apply standard security headers for file downloads."""
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response['X-Content-Type-Options'] = 'nosniff'
    response['X-Download-Options'] = 'noopen'
