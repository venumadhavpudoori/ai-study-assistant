import uuid
from app.core.config import settings

def validate_pdf_mime(content: bytes) -> bool:
    """Verify that the file is actually a PDF using magic bytes."""
    if content.startswith(b"%PDF-"):
        return True
    try:
        import magic
        mime = magic.from_buffer(content, mime=True)
        return mime == "application/pdf"
    except Exception:
        return False

def validate_file_size(content_length: int) -> bool:
    """Verify that the file size is within limits."""
    return content_length <= settings.MAX_UPLOAD_SIZE

def generate_safe_filename(original_filename: str) -> str:
    """Generate a unique UUID-based filename while preserving .pdf extension."""
    return f"{uuid.uuid4()}.pdf"
