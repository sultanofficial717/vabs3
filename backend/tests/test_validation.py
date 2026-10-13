import pytest
from backend.app.schemas.assessment import validate_patient_info, validate_assessment_inputs


def test_validate_patient_info_valid():
    data = {
        "name": "Jordan Doe",
        "age_years": 8,
        "age_months": 3,
        "sex": "Female",
        "respondent": "Father",
    }
    cleaned, errors = validate_patient_info(data)
    assert len(errors) == 0
    assert cleaned["name"] == "Jordan Doe"
    assert cleaned["age_years"] == 8
    assert cleaned["age_months"] == 3
    assert cleaned["sex"] == "Female"


def test_validate_patient_info_missing_name():
    data = {
        "name": "",
        "age_years": 5,
    }
    cleaned, errors = validate_patient_info(data)
    assert any("name or identifier is required" in e.lower() for e in errors)


def test_validate_patient_info_invalid_age():
    data = {
        "name": "Test Child",
        "age_years": -2,
        "age_months": 15,
    }
    cleaned, errors = validate_patient_info(data)
    assert any("age (years) must be between 0 and 90" in e.lower() for e in errors)
    assert any("age (months) must be between 0 and 11" in e.lower() for e in errors)


def test_validate_assessment_inputs_missing_scores():
    payload = {
        "patient_info": {"name": "Test", "age_years": 6},
        "raw_scores": {},
    }
    cleaned, errors = validate_assessment_inputs(payload)
    assert any("at least one subdomain raw score" in e.lower() for e in errors)
