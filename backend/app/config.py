import os
from pathlib import Path

# Paths
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_FOLDER = DATA_DIR / "uploads"
REPORT_FOLDER = DATA_DIR / "reports"

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
REPORT_FOLDER.mkdir(parents=True, exist_ok=True)

# Application Config
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "autism-lens-clinical-secret-key-2026")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB max upload
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
    }
    
    # Storage
    UPLOAD_FOLDER = str(UPLOAD_FOLDER)
    REPORT_FOLDER = str(REPORT_FOLDER)
    
    # Groq API
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
    
    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
