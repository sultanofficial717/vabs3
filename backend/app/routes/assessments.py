import os
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app

from backend.app.config import Config
from backend.app.schemas.assessment import validate_assessment_inputs, validate_patient_info
from backend.app.services.scoring_service import ScoringService
from backend.app.services.interpretation_service import InterpretationService
from backend.app.services.storage_service import AssessmentStorage
from backend.app.reports.pdf_builder import PDFReportBuilder

assessments_bp = Blueprint("assessments", __name__)


@assessments_bp.route("/api/meta", methods=["GET"])
def get_metadata():
    """Retrieve scoring metadata, item descriptions, and age markers."""
    try:
        data = ScoringService.get_metadata()
        return jsonify({"ok": True, "metadata": data}), 200
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Failed to load metadata: {exc}"}), 500


@assessments_bp.route("/api/assessments", methods=["GET"])
def list_assessments():
    """List recent assessments with optional search query and status filter."""
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    items = AssessmentStorage.get_all(search=search, status=status)
    return jsonify({"ok": True, "assessments": items, "total": len(items)}), 200


@assessments_bp.route("/api/assessments/<assessment_id>", methods=["GET"])
def get_assessment_detail(assessment_id: str):
    """Retrieve a single assessment by ID."""
    item = AssessmentStorage.get_by_id(assessment_id)
    if not item:
        return jsonify({"ok": False, "error": "Assessment not found"}), 404
    return jsonify({"ok": True, "assessment": item}), 200


@assessments_bp.route("/api/assessments/<assessment_id>", methods=["DELETE"])
def delete_assessment(assessment_id: str):
    """Delete an assessment record."""
    success = AssessmentStorage.delete(assessment_id)
    if not success:
        return jsonify({"ok": False, "error": "Assessment not found or already deleted"}), 404
    return jsonify({"ok": True, "message": f"Assessment {assessment_id} deleted successfully"}), 200


@assessments_bp.route("/api/patients", methods=["GET"])
def list_patients():
    """List patients derived from assessments."""
    search = request.args.get("search", "").strip()
    patients = AssessmentStorage.get_patients(search=search)
    return jsonify({"ok": True, "patients": patients, "total": len(patients)}), 200


@assessments_bp.route("/api/reports", methods=["GET"])
def list_reports():
    """List available clinical PDF reports."""
    reports = AssessmentStorage.get_reports()
    return jsonify({"ok": True, "reports": reports, "total": len(reports)}), 200


@assessments_bp.route("/api/analytics", methods=["GET"])
def get_analytics():
    """Retrieve aggregate KPI statistics and domain score distributions."""
    stats = AssessmentStorage.get_analytics()
    return jsonify({"ok": True, "analytics": stats}), 200


@assessments_bp.route("/api/assessments/validate", methods=["POST"])
def validate_assessment():
    """
    Step 3: Verification stage.
    Explicitly checks completeness, formats, and returns validated data or actionable errors.
    """
    payload = request.get_json(silent=True) or {}
    cleaned_payload, errors = validate_assessment_inputs(payload)

    if errors:
        return jsonify({
            "ok": False,
            "verified": False,
            "errors": errors,
            "cleaned_data": cleaned_payload,
        }), 422

    return jsonify({
        "ok": True,
        "verified": True,
        "message": "All assessment inputs successfully verified.",
        "cleaned_data": cleaned_payload,
    }), 200


@assessments_bp.route("/api/assessments/score", methods=["POST"])
def score_assessment():
    """
    Step 4: Execute Pearson VABS-3 scoring engine and DSM-5-TR ASD Pattern Engine.
    """
    payload = request.get_json(silent=True) or {}
    cleaned_payload, errors = validate_assessment_inputs(payload)

    if errors:
        return jsonify({
            "ok": False,
            "error": "Validation failed prior to scoring.",
            "errors": errors,
        }), 422

    try:
        result = ScoringService.calculate_assessment(
            patient_info=cleaned_payload["patient_info"],
            raw_scores=cleaned_payload["raw_scores"],
            item_responses=cleaned_payload["item_responses"],
            maladaptive=cleaned_payload["maladaptive"],
        )

        # Persist or update assessment in storage
        aid = payload.get("assessment_id") or f"AL-{uuid.uuid4().hex[:6].upper()}"
        result["assessment_id"] = aid
        intake_method = payload.get("intake_method", "manual")

        record = {
            "assessment_id": aid,
            "patient_info": cleaned_payload["patient_info"],
            "raw_scores": cleaned_payload["raw_scores"],
            "intake_method": intake_method,
            "status": "Completed",
            "verified": True,
            "scores": result["scores"],
            "patterns": result["patterns"],
            "report_generated": False,
            "pdf_filename": None,
        }
        AssessmentStorage.save_or_update(record)

        return jsonify(result), 200
    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": f"Scoring calculation failed: {str(exc)}",
        }), 500


@assessments_bp.route("/api/assessments/report", methods=["POST"])
def generate_report():
    """
    Step 6: Generate clinical narrative and publication-grade PDF report.
    """
    payload = request.get_json(silent=True) or {}
    scores = payload.get("scores")
    patient_info = payload.get("patient_info")
    patterns = payload.get("patterns")
    assessment_id = payload.get("assessment_id") or f"AL-{uuid.uuid4().hex[:6].upper()}"

    if not scores or not patient_info:
        return jsonify({
            "ok": False,
            "error": "Both 'scores' and 'patient_info' are required to generate a report.",
        }), 400

    try:
        # Generate Narrative
        narrative_res = InterpretationService.generate_narrative(
            scores=scores,
            patient_info=patient_info,
            patterns=patterns,
        )
        narrative_text = narrative_res.get("narrative", "")

        # Generate PDF
        assessment_data = {
            "assessment_id": assessment_id,
            "patient_info": patient_info,
            "scores": scores,
            "patterns": patterns or {},
        }

        pdf_path, generated_id = PDFReportBuilder.generate_report(
            assessment_data=assessment_data,
            narrative_text=narrative_text,
        )
        pdf_name = Path(pdf_path).name

        # Update assessment record in storage
        AssessmentStorage.save_or_update({
            "assessment_id": generated_id,
            "patient_info": patient_info,
            "scores": scores,
            "patterns": patterns or {},
            "status": "Completed",
            "report_generated": True,
            "pdf_filename": pdf_name,
        })

        return jsonify({
            "ok": True,
            "assessment_id": generated_id,
            "narrative": narrative_text,
            "narrative_source": narrative_res.get("source"),
            "pdf_filename": pdf_name,
            "download_url": f"/api/assessments/{generated_id}/report",
        }), 200

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": f"Report generation failed: {str(exc)}",
        }), 500


@assessments_bp.route("/api/assessments/<assessment_id>/report", methods=["GET"])
def download_report(assessment_id: str):
    """
    Step 7: Download authorized PDF report.
    """
    safe_id = "".join(c for c in assessment_id if c.isalnum() or c in ("-", "_"))
    report_folder = Path(Config.REPORT_FOLDER)
    pdf_path = report_folder / f"AutismLens_Report_{safe_id}.pdf"

    # Also check if it was named without prefix
    if not pdf_path.exists():
        pdf_path = report_folder / f"{safe_id}.pdf"

    if not pdf_path.exists() or not pdf_path.is_file():
        # Fallback: check if stored assessment has a registered filename
        item = AssessmentStorage.get_by_id(safe_id)
        if item and item.get("pdf_filename"):
            cand = report_folder / item["pdf_filename"]
            if cand.exists():
                pdf_path = cand

    if not pdf_path.exists() or not pdf_path.is_file():
        return jsonify({
            "ok": False,
            "error": "Requested report not found or expired.",
        }), 404

    return send_file(
        str(pdf_path),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"AutismLens_Assessment_Report_{safe_id}.pdf",
    )
