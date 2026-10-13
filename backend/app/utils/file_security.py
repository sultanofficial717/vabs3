import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from backend.app.config import Config

MAGIC_SIGNATURES = {
    "pdf": [b"%PDF"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
}


def is_allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS


def validate_file_magic(file_stream, ext: str) -> bool:
    """Inspect file header magic bytes to verify content authenticity."""
    ext = ext.lower()
    signatures = MAGIC_SIGNATURES.get(ext)
    if not signatures:
        return False
    
    pos = file_stream.tell()
    header = file_stream.read(16)
    file_stream.seek(pos)
    
    for sig in signatures:
        if header.startswith(sig):
            return True
    return False


def save_secure_upload(file_storage, target_dir: str = None) -> tuple[str, str, str]:
    """
    Saves an uploaded file securely:
    - Generates server-controlled UUID filename
    - Verifies extension and magic bytes
    - Returns (saved_absolute_path, safe_original_name, file_extension)
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided for upload.")
        
    orig_name = secure_filename(file_storage.filename) or "document"
    if not is_allowed_file(orig_name):
        raise ValueError("Unsupported file extension. Allowed: PDF, PNG, JPG, JPEG.")
        
    ext = orig_name.rsplit(".", 1)[1].lower()
    
    if not validate_file_magic(file_storage.stream, ext):
        raise ValueError(f"File content does not match expected format for .{ext}.")
        
    target_folder = Path(target_dir or Config.UPLOAD_FOLDER)
    target_folder.mkdir(parents=True, exist_ok=True)
    
    unique_id = uuid.uuid4().hex
    safe_name = f"{unique_id}.{ext}"
    dest_path = target_folder / safe_name
    
    # Save file
    file_storage.save(str(dest_path))
    
    return str(dest_path), orig_name, ext


def cleanup_file(filepath: str) -> None:
    """Safely remove a file if it exists."""
    try:
        p = Path(filepath)
        if p.exists() and p.is_file():
            p.unlink()
    except Exception:
        pass
