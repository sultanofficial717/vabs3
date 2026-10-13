import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.config import DATA_DIR, REPORT_FOLDER

STORAGE_FILE = DATA_DIR / "assessments.json"


class AssessmentStorage:
    """
    Lightweight, persistent local storage for clinical assessments,
    supporting history tracking, patient directory, report catalog, and analytics.
    """

    @classmethod
    def _init_storage(cls) -> List[Dict[str, Any]]:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not STORAGE_FILE.exists():
            # Seed initial clinical sample records for demonstration
            initial_data = [
                {
                    "assessment_id": "AL-84291",
                    "patient_info": {
                        "name": "Leo Vance",
                        "age_years": 7,
                        "age_months": 6,
                        "sex": "Male",
                        "respondent": "Elena Vance",
                        "relationship": "Mother",
                        "test_date": "2026-10-08",
                        "referral": "Evaluation of social-communication delay and repetitive behaviors",
                    },
                    "intake_method": "document_upload",
                    "status": "Completed",
                    "verified": True,
                    "created_at": "2026-10-08T10:15:00",
                    "scores": {
                        "domains": {
                            "COM": {"ss": 68, "band": "Moderately Low", "percentile": "2"},
                            "DLS": {"ss": 78, "band": "Moderately Low", "percentile": "7"},
                            "SOC": {"ss": 62, "band": "Low", "percentile": "1"},
                            "MOT": {"ss": 92, "band": "Adequate", "percentile": "30"},
                        },
                        "composite": {"abc": 65, "abc_band": "Low", "percentile": "1"},
                        "mean_ss": 75,
                    },
                    "patterns": {
                        "asd_profile_likelihood": {
                            "label": "Strongly Consistent with ASD-Related Adaptive Profile",
                            "color": "danger",
                        },
                        "score_range": 30,
                    },
                    "report_generated": True,
                    "pdf_filename": "AutismLens_Report_AL-84291.pdf",
                },
                {
                    "assessment_id": "AL-19402",
                    "patient_info": {
                        "name": "Maya Chen",
                        "age_years": 5,
                        "age_months": 2,
                        "sex": "Female",
                        "respondent": "David Chen",
                        "relationship": "Father",
                        "test_date": "2026-10-09",
                        "referral": "School readiness and peer interaction assessment",
                    },
                    "intake_method": "manual",
                    "status": "Completed",
                    "verified": True,
                    "created_at": "2026-10-09T14:30:00",
                    "scores": {
                        "domains": {
                            "COM": {"ss": 82, "band": "Adequate", "percentile": "12"},
                            "DLS": {"ss": 85, "band": "Adequate", "percentile": "16"},
                            "SOC": {"ss": 71, "band": "Moderately Low", "percentile": "3"},
                            "MOT": {"ss": 88, "band": "Adequate", "percentile": "21"},
                        },
                        "composite": {"abc": 78, "abc_band": "Moderately Low", "percentile": "7"},
                        "mean_ss": 81,
                    },
                    "patterns": {
                        "asd_profile_likelihood": {
                            "label": "Partially Consistent with ASD-Related Adaptive Profile",
                            "color": "warning",
                        },
                        "score_range": 17,
                    },
                    "report_generated": True,
                    "pdf_filename": "AutismLens_Report_AL-19402.pdf",
                },
                {
                    "assessment_id": "AL-62019",
                    "patient_info": {
                        "name": "Ethan Brooks",
                        "age_years": 8,
                        "age_months": 4,
                        "sex": "Male",
                        "respondent": "Sarah Brooks",
                        "relationship": "Mother",
                        "test_date": "2026-10-10",
                        "referral": "Annual adaptive skills review",
                    },
                    "intake_method": "document_upload",
                    "status": "Awaiting Review",
                    "verified": False,
                    "created_at": "2026-10-10T11:00:00",
                    "scores": None,
                    "patterns": None,
                    "report_generated": False,
                    "pdf_filename": None,
                },
            ]
            cls._save_all(initial_data)
            return initial_data

        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def _save_all(cls, items: List[Dict[str, Any]]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    @classmethod
    def get_all(cls, search: str = "", status: str = "") -> List[Dict[str, Any]]:
        items = cls._init_storage()
        filtered = items
        if search:
            q = search.lower()
            filtered = [
                i for i in filtered
                if q in i.get("assessment_id", "").lower()
                or q in i.get("patient_info", {}).get("name", "").lower()
            ]
        if status and status != "all":
            filtered = [i for i in filtered if i.get("status", "").lower() == status.lower()]

        # Sort newest first
        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return filtered

    @classmethod
    def get_by_id(cls, assessment_id: str) -> Optional[Dict[str, Any]]:
        items = cls._init_storage()
        for i in items:
            if i.get("assessment_id", "").upper() == assessment_id.upper():
                return i
        return None

    @classmethod
    def save_or_update(cls, assessment: Dict[str, Any]) -> Dict[str, Any]:
        items = cls._init_storage()
        aid = assessment.get("assessment_id")
        if not aid:
            aid = f"AL-{uuid.uuid4().hex[:6].upper()}"
            assessment["assessment_id"] = aid

        if not assessment.get("created_at"):
            assessment["created_at"] = datetime.now().isoformat()

        updated = False
        for idx, existing in enumerate(items):
            if existing.get("assessment_id", "").upper() == aid.upper():
                # Merge existing fields with new values
                merged = {**existing, **assessment}
                items[idx] = merged
                updated = True
                break

        if not updated:
            items.insert(0, assessment)

        cls._save_all(items)
        return assessment

    @classmethod
    def delete(cls, assessment_id: str) -> bool:
        items = cls._init_storage()
        before = len(items)
        items = [i for i in items if i.get("assessment_id", "").upper() != assessment_id.upper()]
        if len(items) < before:
            cls._save_all(items)
            return True
        return False

    @classmethod
    def get_patients(cls, search: str = "") -> List[Dict[str, Any]]:
        items = cls._init_storage()
        patients_map = {}
        for item in items:
            p = item.get("patient_info", {})
            name = p.get("name", "Unknown")
            if not name:
                continue
            key = name.lower()
            if key not in patients_map:
                patients_map[key] = {
                    "name": name,
                    "age_years": p.get("age_years", 0),
                    "age_months": p.get("age_months", 0),
                    "sex": p.get("sex", "Unspecified"),
                    "total_assessments": 0,
                    "latest_assessment_id": item.get("assessment_id"),
                    "latest_date": item.get("created_at", "")[:10],
                    "latest_status": item.get("status", "Draft"),
                    "latest_abc": (item.get("scores") or {}).get("composite", {}).get("abc", "-") if item.get("scores") else "-",
                }
            patients_map[key]["total_assessments"] += 1

        patients_list = list(patients_map.values())
        if search:
            q = search.lower()
            patients_list = [p for p in patients_list if q in p["name"].lower()]
        return sorted(patients_list, key=lambda x: x["name"])

    @classmethod
    def get_reports(cls) -> List[Dict[str, Any]]:
        items = cls._init_storage()
        reports = []
        for item in items:
            if item.get("report_generated") and item.get("pdf_filename"):
                reports.append({
                    "assessment_id": item.get("assessment_id"),
                    "patient_name": item.get("patient_info", {}).get("name", "Unknown"),
                    "date": item.get("created_at", "")[:10],
                    "pdf_filename": item.get("pdf_filename"),
                    "download_url": f"/api/assessments/{item.get('assessment_id')}/report",
                    "status": "Available",
                })
        return sorted(reports, key=lambda x: x["date"], reverse=True)

    @classmethod
    def get_analytics(cls) -> Dict[str, Any]:
        items = cls._init_storage()
        total = len(items)
        completed = sum(1 for i in items if i.get("status") == "Completed")
        awaiting_review = sum(1 for i in items if i.get("status") in ("Awaiting Review", "Draft"))
        reports_count = sum(1 for i in items if i.get("report_generated"))

        intake_breakdown = {
            "manual": sum(1 for i in items if i.get("intake_method") == "manual"),
            "document_upload": sum(1 for i in items if i.get("intake_method") == "document_upload"),
        }

        # Average Domain Scores across completed assessments
        domain_sums = {"COM": 0, "DLS": 0, "SOC": 0, "MOT": 0, "ABC": 0}
        scored_count = 0
        for i in items:
            scores = i.get("scores")
            if scores and scores.get("domains"):
                doms = scores["domains"]
                if all(doms.get(d, {}).get("ss") is not None for d in ["COM", "DLS", "SOC"]):
                    domain_sums["COM"] += doms["COM"]["ss"]
                    domain_sums["DLS"] += doms["DLS"]["ss"]
                    domain_sums["SOC"] += doms["SOC"]["ss"]
                    if doms.get("MOT", {}).get("ss"):
                        domain_sums["MOT"] += doms["MOT"]["ss"]
                    comp = scores.get("composite", {})
                    if comp and comp.get("abc"):
                        domain_sums["ABC"] += comp["abc"]
                    scored_count += 1

        avg_scores = {}
        if scored_count > 0:
            avg_scores = {k: round(v / scored_count, 1) for k, v in domain_sums.items()}

        return {
            "total_assessments": total,
            "completed_assessments": completed,
            "awaiting_review": awaiting_review,
            "reports_generated": reports_count,
            "intake_breakdown": intake_breakdown,
            "average_domain_scores": avg_scores,
            "scored_sample_size": scored_count,
        }
