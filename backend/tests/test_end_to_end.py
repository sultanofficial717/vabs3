import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_full_workflow_end_to_end(client):
    # 1. Step 3 - Input Verification
    payload = {
        "patient_info": {
            "name": "Jordan EndToEnd",
            "age_years": 7,
            "age_months": 5,
            "sex": "Male",
            "respondent": "Mother",
            "relationship": "Biological Parent",
            "test_date": "2026-10-10",
            "referral": "Vineland-3 ASD Decision Support Testing",
        },
        "raw_scores": {
            "rec": 28, "exp": 32, "wrn": 14,
            "per": 38, "dom": 18, "cmm": 12,
            "ipr": 16, "pla": 12, "cop": 10,
            "gmo": 36, "fmo": 26,
        },
        "maladaptive": {
            "provided": True,
            "int": [1, 2, 0, 1, 1, 0, 2, 0, 1, 1, 1, 0, 0],
            "ext": [1, 1, 0, 0, 1, 2, 0, 0, 2, 0, 0],
            "critical": [2, 0, 1, 2, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        },
        "verified": True,
    }

    val_res = client.post("/api/assessments/validate", json=payload)
    assert val_res.status_code == 200
    val_data = val_res.get_json()
    assert val_data["ok"] is True
    assert val_data["verified"] is True

    # 2. Step 4 - Scoring
    score_res = client.post("/api/assessments/score", json=payload)
    assert score_res.status_code == 200
    score_data = score_res.get_json()
    assert score_data["ok"] is True
    assert "scores" in score_data
    assert "patterns" in score_data
    assert score_data["scores"]["composite"]["abc"] is not None

    # 3. Step 6 - Report Generation
    rep_payload = {
        "assessment_id": "TEST_E2E_01",
        "patient_info": score_data["patient_info"],
        "scores": score_data["scores"],
        "patterns": score_data["patterns"],
    }
    rep_res = client.post("/api/assessments/report", json=rep_payload)
    assert rep_res.status_code == 200
    rep_data = rep_res.get_json()
    assert rep_data["ok"] is True
    assert rep_data["assessment_id"] == "TEST_E2E_01"
    assert rep_data["download_url"] == "/api/assessments/TEST_E2E_01/report"

    # 4. Step 7 - Report Download
    dl_res = client.get(rep_data["download_url"])
    assert dl_res.status_code == 200
    assert dl_res.headers["Content-Type"] == "application/pdf"
    assert len(dl_res.data) > 1000
