from typing import Any, Dict, List, Optional
from datetime import datetime


class ValidationError(Exception):
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or [message]


def validate_patient_info(patient: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    """
    Validates and normalizes patient info fields.
    Returns (cleaned_dict, list_of_errors).
    """
    errors = []
    cleaned = {}
    
    # Name / Identifier
    name = str(patient.get("name", "")).strip()
    if not name:
        errors.append("Patient name or identifier is required.")
    cleaned["name"] = name
    
    # Age Years
    age_years_raw = patient.get("age_years")
    if age_years_raw is None or str(age_years_raw).strip() == "":
        errors.append("Patient age (years) is required.")
        cleaned["age_years"] = 0
    else:
        try:
            ay = int(float(age_years_raw))
            if ay < 0 or ay > 90:
                errors.append("Patient age (years) must be between 0 and 90.")
            cleaned["age_years"] = ay
        except (ValueError, TypeError):
            errors.append("Patient age (years) must be a valid number.")
            cleaned["age_years"] = 0
            
    # Age Months
    age_months_raw = patient.get("age_months", 0)
    try:
        am = int(float(age_months_raw)) if age_months_raw not in (None, "") else 0
        if am < 0 or am > 11:
            errors.append("Patient age (months) must be between 0 and 11.")
        cleaned["age_months"] = am
    except (ValueError, TypeError):
        errors.append("Patient age (months) must be between 0 and 11.")
        cleaned["age_months"] = 0
        
    # Sex
    sex = str(patient.get("sex", "")).strip().capitalize()
    if sex not in ("Male", "Female", "Other", ""):
        cleaned["sex"] = "Other"
    else:
        cleaned["sex"] = sex or "Unspecified"
        
    # Informant / Respondent
    respondent = str(patient.get("respondent", "")).strip()
    cleaned["respondent"] = respondent or "Caregiver"
    
    relationship = str(patient.get("relationship", "")).strip()
    cleaned["relationship"] = relationship or "Parent/Guardian"
    
    # Test Date
    test_date = str(patient.get("test_date", "")).strip()
    if not test_date:
        cleaned["test_date"] = datetime.now().strftime("%Y-%m-%d")
    else:
        cleaned["test_date"] = test_date
        
    # Referral reason
    cleaned["referral"] = str(patient.get("referral", "")).strip() or "Comprehensive developmental and adaptive evaluation"
    
    return cleaned, errors


def validate_assessment_inputs(payload: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    """
    Validates complete assessment payload before scoring.
    Ensures either raw scores or item responses are supplied with acceptable values.
    """
    all_errors = []
    
    patient_info, p_errors = validate_patient_info(payload.get("patient_info", {}))
    all_errors.extend(p_errors)
    
    raw_scores = payload.get("raw_scores") or {}
    item_responses = payload.get("item_responses") or {}
    maladaptive = payload.get("maladaptive") or {}
    
    # Check that at least some domain/subdomain data is provided
    has_raw = any(raw_scores.get(code) not in (None, "") for code in raw_scores)
    has_items = any(isinstance(item_responses.get(code), list) and len(item_responses[code]) > 0 for code in item_responses)
    
    if not has_raw and not has_items:
        all_errors.append("At least one subdomain raw score or item-response vector must be provided.")
        
    cleaned_payload = {
        "patient_info": patient_info,
        "raw_scores": raw_scores,
        "item_responses": item_responses,
        "maladaptive": maladaptive,
        "verified": bool(payload.get("verified", False)),
    }
    
    return cleaned_payload, all_errors
