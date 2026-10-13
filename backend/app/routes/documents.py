import os
from flask import Blueprint, request, jsonify
from backend.app.utils.file_security import save_secure_upload, cleanup_file
from backend.app.document_processing.extractor import DocumentExtractor

documents_bp = Blueprint("documents", __name__)


@documents_bp.route("/api/documents/extract", methods=["POST"])
def extract_document():
    """
    Upload and extract patient demographics and assessment scores
    from an evaluation PDF or photographed sheet.
    """
    if "file" not in request.files:
        return jsonify({
            "ok": False,
            "error": "No file uploaded. Please select a PDF or image file.",
        }), 400

    file_obj = request.files["file"]
    if not file_obj.filename:
        return jsonify({
            "ok": False,
            "error": "Empty filename provided.",
        }), 400

    try:
        saved_path, original_name, ext = save_secure_upload(file_obj)
    except ValueError as val_err:
        return jsonify({
            "ok": False,
            "error": str(val_err),
        }), 400
    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": f"Failed to save uploaded file: {exc}",
        }), 500

    try:
        extraction_result = DocumentExtractor.extract_from_file(saved_path)
        extraction_result["original_filename"] = original_name
        extraction_result["ok"] = True
        return jsonify(extraction_result), 200
    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": f"Document extraction failed: {str(exc)}",
        }), 422
    finally:
        # Retention policy: Temporary uploaded files are cleaned up after processing to ensure privacy
        cleanup_file(saved_path)
