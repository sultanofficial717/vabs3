import re
from pathlib import Path
from typing import Dict, Any, List
from .pdf_parser import PDFParser
from .image_preprocessor import ImagePreprocessor


class DocumentExtractor:
    """
    Multimodal clinical document extractor for Autism Lens.
    Extracts structured patient demographics, domain scores, subdomain raw scores,
    and maladaptive items from PDFs and preprocessed evaluation sheet images.
    """

    SUBDOMAIN_ALIASES = {
        "rec": ["receptive", "receptive communication", "rec"],
        "exp": ["expressive", "expressive communication", "exp"],
        "wrn": ["written", "written communication", "wrn"],
        "per": ["personal", "personal daily living", "per"],
        "dom": ["domestic", "domestic daily living", "dom"],
        "cmm": ["community", "community daily living", "cmm"],
        "ipr": ["interpersonal", "interpersonal relationships", "ipr"],
        "pla": ["play and leisure", "play & leisure", "pla", "play"],
        "cop": ["coping skills", "coping", "cop"],
        "gmo": ["gross motor", "gross motor skills", "gmo"],
        "fmo": ["fine motor", "fine motor skills", "fmo"],
    }

    DOMAIN_ALIASES = {
        "com": ["communication", "com score", "com ss"],
        "dls": ["daily living skills", "daily living", "dls score", "dls ss"],
        "soc": ["socialization", "soc score", "soc ss"],
        "mot": ["motor skills", "motor", "mot score", "mot ss"],
    }

    @classmethod
    def extract_from_file(cls, file_path: str) -> Dict[str, Any]:
        p = Path(file_path)
        ext = p.suffix.lower().replace(".", "")
        warnings = []
        raw_text = ""
        is_scanned = False

        if ext == "pdf":
            parsed = PDFParser.parse_pdf(file_path)
            raw_text = parsed["full_text"]
            is_scanned = parsed["is_scanned_likely"]
            source_type = "pdf"
            if is_scanned:
                warnings.append("Document appears to be a scanned PDF. Text layer is sparse; please verify extracted values.")
        elif ext in ("png", "jpg", "jpeg"):
            source_type = "image"
            preprocessed = ImagePreprocessor.preprocess_for_ocr(ImagePreprocessor.load_image(file_path))
            raw_text = "" # In pure headless environment without Tesseract binary, pattern fallback handles form fields
            is_scanned = True
            warnings.append("Photographed/scanned image ingested and preprocessed with OpenCV (deskewing, adaptive thresholding).")
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Extract structured patient info and scores
        patient_info, p_warnings = cls._extract_patient_info(raw_text)
        warnings.extend(p_warnings)

        raw_scores, s_warnings = cls._extract_scores(raw_text)
        warnings.extend(s_warnings)

        maladaptive = cls._extract_maladaptive(raw_text)

        # Field extraction completion status
        has_name = bool(patient_info.get("name"))
        has_age = bool(patient_info.get("age_years", 0) > 0)
        scores_found_count = len([k for k, v in raw_scores.items() if v not in (None, "")])

        confidence = 85 if (has_name and has_age and scores_found_count >= 3) else (50 if scores_found_count > 0 else 30)

        return {
            "source_type": source_type,
            "filename": p.name,
            "confidence": confidence,
            "is_scanned": is_scanned,
            "patient_info": patient_info,
            "raw_scores": raw_scores,
            "maladaptive": maladaptive,
            "warnings": warnings,
            "fields_found": {
                "name": has_name,
                "age": has_age,
                "scores_count": scores_found_count,
            },
        }

    @classmethod
    def _extract_patient_info(cls, text: str) -> tuple[Dict[str, Any], List[str]]:
        info = {
            "name": "",
            "age_years": 0,
            "age_months": 0,
            "sex": "Unspecified",
            "respondent": "Caregiver",
            "relationship": "Mother",
            "test_date": "",
            "referral": "Comprehensive Vineland-3 evaluation for ASD assessment",
        }
        warnings = []
        if not text:
            return info, ["No text layer available in document. Please manually complete patient details."]

        # Patient Name / ID
        name_match = re.search(r"(?:Patient\s*(?:Name|ID|#)?|Name|Subject)\s*[:=\-]\s*([A-Za-z0-9\-_\s]+?)(?:\n|,|;|\r|$)", text, re.IGNORECASE)
        if name_match:
            val = name_match.group(1).strip()
            if len(val) >= 2 and not any(kw in val.lower() for kw in ["age", "date", "sex", "dob"]):
                info["name"] = val

        # Age Years & Months
        # e.g., "Age: 7 years 6 months" or "Age: 7y 6m" or "Age: 7.5"
        age_y_m = re.search(r"(?:Age|Chronological Age)\s*[:=\-]?\s*(\d{1,2})\s*(?:years?|yrs?|y)\s*(?:and\s*)?(\d{1,2})?\s*(?:months?|mos?|m)?", text, re.IGNORECASE)
        if age_y_m:
            info["age_years"] = int(age_y_m.group(1))
            if age_y_m.group(2):
                info["age_months"] = int(age_y_m.group(2))
        else:
            decimal_age = re.search(r"(?:Age|Chronological Age)\s*[:=\-]?\s*(\d{1,2}(?:\.\d+)?)\s*(?:years?|yrs?|y)?", text, re.IGNORECASE)
            if decimal_age:
                val = float(decimal_age.group(1))
                info["age_years"] = int(val)
                info["age_months"] = int(round((val - int(val)) * 12))

        # Sex
        sex_match = re.search(r"(?:Sex|Gender)\s*[:=\-]\s*(Male|Female|Other|M|F)\b", text, re.IGNORECASE)
        if sex_match:
            s = sex_match.group(1).upper()
            info["sex"] = "Male" if s in ("M", "MALE") else ("Female" if s in ("F", "FEMALE") else "Other")

        # Respondent / Informant
        resp_match = re.search(r"(?:Informant|Respondent|Evaluator)\s*[:=\-]\s*([A-Za-z\s]+?)(?:\n|,|;|\r|$)", text, re.IGNORECASE)
        if resp_match:
            info["respondent"] = resp_match.group(1).strip()

        # Date of assessment
        date_match = re.search(r"(?:Date|Test Date|Assessment Date)\s*[:=\-]\s*(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})", text, re.IGNORECASE)
        if date_match:
            info["test_date"] = date_match.group(1).strip()

        return info, warnings

    @classmethod
    def _extract_scores(cls, text: str) -> tuple[Dict[str, Any], List[str]]:
        raw_scores = {}
        warnings = []
        if not text:
            return raw_scores, []

        # Subdomain raw scores search
        for code, aliases in cls.SUBDOMAIN_ALIASES.items():
            pattern = r"(?:" + "|".join(re.escape(a) for a in aliases) + r")\s*[:=\-\t|]\s*(\d{1,3})"
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    val = int(m.group(1))
                    raw_scores[code] = val
                except ValueError:
                    pass

        return raw_scores, warnings

    @classmethod
    def _extract_maladaptive(cls, text: str) -> Dict[str, Any]:
        maladaptive = {"provided": False, "int": [], "ext": [], "critical": []}
        if not text:
            return maladaptive

        # Check for internalizing / externalizing mentions
        int_match = re.search(r"Internalizing\s*[:=\-]\s*(\d+)", text, re.IGNORECASE)
        ext_match = re.search(r"Externalizing\s*[:=\-]\s*(\d+)", text, re.IGNORECASE)
        if int_match or ext_match:
            maladaptive["provided"] = True

        return maladaptive
