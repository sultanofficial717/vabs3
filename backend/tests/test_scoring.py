import pytest
from backend.app.services.scoring_service import ScoringService


def test_scoring_known_profile():
    patient_info = {
        "name": "Alex Test",
        "age_years": 7,
        "age_months": 6,
        "sex": "Male",
        "respondent": "Mother",
    }
    raw_scores = {
        "rec": 28, "exp": 32, "wrn": 14,
        "per": 38, "dom": 18, "cmm": 12,
        "ipr": 16, "pla": 12, "cop": 10,
        "gmo": 36, "fmo": 26,
    }

    result = ScoringService.calculate_assessment(patient_info, raw_scores)
    assert result["ok"] is True
    assert "scores" in result
    scores = result["scores"]

    # Check domains exist
    domains = scores["domains"]
    assert "COM" in domains
    assert "DLS" in domains
    assert "SOC" in domains
    assert "MOT" in domains

    # Check Standard Scores and Confidence Intervals
    assert isinstance(domains["COM"]["ss"], int)
    assert isinstance(domains["SOC"]["ss"], int)
    assert "90" in domains["COM"]["ci"]

    # Check Composite (ABC)
    composite = scores["composite"]
    assert composite["abc"] is not None
    assert composite["percentile"] != "-"

    # Check Strengths and Weaknesses
    assert len(scores["strength_weakness"]) == 4

    # Check clinical safeguard
    assert "decision support" in result["clinical_safeguard"].lower()
