import os
from datetime import datetime
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint indicating system status and active capabilities."""
    groq_configured = bool(os.environ.get("GROQ_API_KEY", "").strip())
    
    return jsonify({
        "status": "healthy",
        "service": "Autism Lens Clinical Decision Support API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "capabilities": {
            "deterministic_vabs3_scoring": True,
            "asd_pattern_engine": True,
            "opencv_document_preprocessing": True,
            "multipage_pdf_parsing": True,
            "reportlab_pdf_export": True,
            "groq_llm_interpreter": groq_configured,
            "deterministic_offline_synthesis": True,
        },
    }), 200
