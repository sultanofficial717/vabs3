import pytest
from pathlib import Path
from backend.app.services.scoring_service import ScoringService
from backend.app.services.interpretation_service import InterpretationService
from backend.app.reports.pdf_builder import PDFReportBuilder


def test_narrative_synthesis_offline():
    patient_info = {
        "name": "Sammy Test",
        "age_years": 6,
        "age_months": 2,
        "sex": "Female",
        "respondent": "Father",
    }
    raw_scores = {"rec": 20, "exp": 25, "ipr": 12, "per": 28}
    result = ScoringService.calculate_assessment(patient_info, raw_scores)

    narrative_res = InterpretationService.generate_narrative(
        scores=result["scores"],
        patient_info=patient_info,
        patterns=result["patterns"],
    )
    assert "narrative" in narrative_res
    text = narrative_res["narrative"]
    assert "Section 1: Referral Context" in text
    assert "Section 7: Cross-Domain Pattern Analysis" in text
    assert "CLINICAL DISCLAIMER" in text


def test_pdf_report_generation(tmp_path):
    patient_info = {
        "name": "Morgan Sample",
        "age_years": 7,
        "age_months": 0,
        "sex": "Male",
        "respondent": "Mother",
    }
    raw_scores = {"rec": 30, "exp": 35, "ipr": 15, "per": 40}
    result = ScoringService.calculate_assessment(patient_info, raw_scores)

    assessment_data = {
        "assessment_id": "TEST1234",
        "patient_info": patient_info,
        "scores": result["scores"],
        "patterns": result["patterns"],
    }
    narrative_text = "### Section 1: Referral Context\nEvaluation completed.\n\n### Section 2: Communication\nAdequate."

    pdf_path, aid = PDFReportBuilder.generate_report(
        assessment_data=assessment_data,
        narrative_text=narrative_text,
        output_dir=str(tmp_path),
    )
    p = Path(pdf_path)
    assert p.exists()
    assert p.is_file()
    assert p.stat().st_size > 1000  # ReportLab PDF with tables has substantial byte size
    assert aid == "TEST1234"
