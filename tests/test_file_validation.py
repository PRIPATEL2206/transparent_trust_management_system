import io
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from services.file_validators import (
    validate_upload_image,
    validate_upload_document,
    BLOCKED_EXTENSIONS,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_DOCUMENT_TYPES,
)


class TestValidateUploadImage:

    def test_valid_jpeg_passes(self):
        file = SimpleUploadedFile(
            'photo.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 100,
            content_type='image/jpeg'
        )
        validate_upload_image(file)

    def test_valid_png_passes(self):
        file = SimpleUploadedFile(
            'icon.png', b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
            content_type='image/png'
        )
        validate_upload_image(file)

    def test_rejects_exe_extension(self):
        file = SimpleUploadedFile(
            'malware.exe', b'\x00' * 100,
            content_type='image/jpeg'
        )
        with pytest.raises(ValidationError, match='not allowed'):
            validate_upload_image(file)

    def test_rejects_bat_extension(self):
        file = SimpleUploadedFile(
            'script.bat', b'\x00' * 100,
            content_type='image/png'
        )
        with pytest.raises(ValidationError, match='not allowed'):
            validate_upload_image(file)

    def test_rejects_php_extension(self):
        file = SimpleUploadedFile(
            'shell.php', b'<?php system("id"); ?>',
            content_type='image/jpeg'
        )
        with pytest.raises(ValidationError, match='not allowed'):
            validate_upload_image(file)

    def test_rejects_wrong_content_type(self):
        file = SimpleUploadedFile(
            'doc.pdf', b'%PDF-1.4' + b'\x00' * 100,
            content_type='application/pdf'
        )
        with pytest.raises(ValidationError, match='not permitted'):
            validate_upload_image(file)

    def test_rejects_oversized_file(self):
        file = SimpleUploadedFile(
            'huge.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * (6 * 1024 * 1024),
            content_type='image/jpeg'
        )
        with pytest.raises(ValidationError, match='exceeds maximum size'):
            validate_upload_image(file)

    def test_rejects_mz_header(self):
        file = SimpleUploadedFile(
            'fake.jpg', b'MZ' + b'\x00' * 100,
            content_type='image/jpeg'
        )
        with pytest.raises(ValidationError, match='Executable'):
            validate_upload_image(file)

    def test_rejects_elf_header(self):
        file = SimpleUploadedFile(
            'fake.png', b'\x7fELF' + b'\x00' * 100,
            content_type='image/png'
        )
        with pytest.raises(ValidationError, match='Executable'):
            validate_upload_image(file)

    def test_none_file_passes(self):
        validate_upload_image(None)

    def test_webp_allowed(self):
        file = SimpleUploadedFile(
            'photo.webp', b'RIFF' + b'\x00' * 100,
            content_type='image/webp'
        )
        validate_upload_image(file)


class TestValidateUploadDocument:

    def test_pdf_allowed(self):
        file = SimpleUploadedFile(
            'report.pdf', b'%PDF-1.4' + b'\x00' * 100,
            content_type='application/pdf'
        )
        validate_upload_document(file)

    def test_image_allowed_as_document(self):
        file = SimpleUploadedFile(
            'scan.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 100,
            content_type='image/jpeg'
        )
        validate_upload_document(file)

    def test_rejects_html_extension(self):
        file = SimpleUploadedFile(
            'page.html', b'<html></html>',
            content_type='text/html'
        )
        with pytest.raises(ValidationError, match='not allowed'):
            validate_upload_document(file)

    def test_rejects_svg_extension(self):
        file = SimpleUploadedFile(
            'vector.svg', b'<svg></svg>',
            content_type='image/svg+xml'
        )
        with pytest.raises(ValidationError, match='not allowed'):
            validate_upload_document(file)

    def test_10mb_limit(self):
        file = SimpleUploadedFile(
            'bigdoc.pdf', b'%PDF-1.4' + b'\x00' * (11 * 1024 * 1024),
            content_type='application/pdf'
        )
        with pytest.raises(ValidationError, match='exceeds maximum size'):
            validate_upload_document(file)

    def test_5mb_file_passes_document_validation(self):
        file = SimpleUploadedFile(
            'medium.pdf', b'%PDF-1.4' + b'\x00' * (5 * 1024 * 1024),
            content_type='application/pdf'
        )
        validate_upload_document(file)

    def test_rejects_jar_extension(self):
        file = SimpleUploadedFile(
            'payload.jar', b'PK\x03\x04' + b'\x00' * 100,
            content_type='application/pdf'
        )
        with pytest.raises(ValidationError, match='not allowed'):
            validate_upload_document(file)


class TestBlockedExtensions:

    def test_all_dangerous_extensions_blocked(self):
        dangerous = ['.exe', '.bat', '.cmd', '.sh', '.ps1', '.php', '.py', '.rb', '.pl']
        for ext in dangerous:
            assert ext in BLOCKED_EXTENSIONS

    def test_safe_extensions_not_blocked(self):
        safe = ['.jpg', '.png', '.pdf', '.docx', '.txt']
        for ext in safe:
            assert ext not in BLOCKED_EXTENSIONS
