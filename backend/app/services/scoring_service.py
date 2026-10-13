import sys
from pathlib import Path
from typing import Dict, Any

# Ensure project root is in sys.path to access root scoring modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import norms
import norms_tables
import scoring
import pattern_engine
import meta
import items as item_defs
import age_markers


# --------------------------------------------------------------------------
# Normative Lookup Alignment Patch
# Corrects Table B.3 age group keys (Table B.3 has 6-month brackets for 6-9y)
# and ensures resilient fallback to the nearest age bracket if lookup misses.
# --------------------------------------------------------------------------
def _aligned_get_age_key_b3(age_years, age_months):
    total_months = age_years * 12 + age_months
    if total_months < 12:
        return "0:0-0:11"
    if total_months < 24:
        return "1:0-1:11"
    if total_months < 36:
        return "2:0-2:11"
    if 36 <= total_months <= 39:
        return "3:0-3:3"
    if 40 <= total_months <= 43:
        return "3:4-3:7"
    if 44 <= total_months <= 47:
        return "3:8-3:11"
    if 48 <= total_months <= 53:
        return "4:0-4:5"
    if 54 <= total_months <= 59:
        return "4:6-4:11"
    if 60 <= total_months <= 65:
        return "5:0-5:5"
    if 66 <= total_months <= 71:
        return "5:6-5:11"
    if 72 <= total_months <= 77:
        return "6:0-6:5"
    if 78 <= total_months <= 83:
        return "6:6-6:11"
    if 84 <= total_months <= 89:
        return "7:0-7:5"
    if 90 <= total_months <= 95:
        return "7:6-7:11"
    if 96 <= total_months <= 101:
        return "8:0-8:5"
    if 102 <= total_months <= 107:
        return "8:6-8:11"
    if 108 <= total_months <= 113:
        return "9:0-9:5"
    if 114 <= total_months <= 119:
        return "9:6-9:11"
    if 120 <= total_months <= 131:
        return "10:0-10:11"
    if 132 <= total_months <= 143:
        return "11:0-11:11"
    if 144 <= total_months <= 155:
        return "12:0-12:11"
    if 156 <= total_months <= 167:
        return "13:0-13:11"
    if 168 <= total_months <= 179:
        return "14:0-14:11"
    if 180 <= total_months <= 191:
        return "15:0-15:11"
    if 192 <= total_months <= 203:
        return "16:0-16:11"
    if 204 <= total_months <= 227:
        return "17:0-18:11"
    if 228 <= total_months <= 251:
        return "19:0-20:11"
    if 252 <= total_months <= 599:
        return "21:0-49:11"
    if 600 <= total_months <= 839:
        return "50:0-69:11"
    return "70-90+"


def _find_closest_b3_key(age_years, age_months):
    total = age_years * 12 + age_months
    def key_months(k):
        if "-" in k:
            part = k.split("-")[0]
        else:
            part = k
        if ":" in part:
            y, m = part.split(":")
            return int(y) * 12 + int(m)
        return 70 * 12
    return min(norms_tables.TABLE_B3.keys(), key=lambda k: abs(key_months(k) - total))


# Monkeypatch norms module
norms.get_age_key_b3 = _aligned_get_age_key_b3

_orig_v_sum_to_ss = norms.v_sum_to_standard_score
def _safe_v_sum_to_ss(domain, v_sum, age_years, age_months):
    age_key = _aligned_get_age_key_b3(age_years, age_months)
    if not age_key or age_key not in norms_tables.TABLE_B3:
        age_key = _find_closest_b3_key(age_years, age_months)
    
    domain_col = {
        "com": "com_sum", "dls": "dls_sum", "soc": "soc_sum", "mot": "mot_sum"
    }.get(domain.lower())
    if not domain_col or age_key not in norms_tables.TABLE_B3:
        return (None, None)

    age_table = norms_tables.TABLE_B3[age_key]
    best_ss = None
    best_dist = float("inf")
    for ss_str, row in age_table.items():
        ss = int(ss_str)
        col_val = row.get(domain_col, "\u2014")
        parsed = norms.parse_range(col_val)
        if parsed is None:
            continue
        lo, hi = parsed
        if lo <= v_sum <= hi:
            return (ss, row.get("percentile", "<1"))
        dist = min(abs(v_sum - lo), abs(v_sum - hi))
        if dist < best_dist:
            best_dist = dist
            best_ss = (ss, row.get("percentile", "<1"))
    return best_ss or (None, None)

norms.v_sum_to_standard_score = _safe_v_sum_to_ss

_orig_sum_ss_to_abc = norms.sum_ss_to_abc
def _safe_sum_ss_to_abc(ss_sum, age_years, age_months):
    age_key = _aligned_get_age_key_b3(age_years, age_months)
    if not age_key or age_key not in norms_tables.TABLE_B3:
        age_key = _find_closest_b3_key(age_years, age_months)

    if age_key not in norms_tables.TABLE_B3:
        return (None, None)

    age_table = norms_tables.TABLE_B3[age_key]
    best_abc = None
    best_dist = float("inf")
    for ss_str, row in age_table.items():
        ss = int(ss_str)
        abc_val = row.get("abc_sum", "\u2014")
        parsed = norms.parse_range(abc_val)
        if parsed is None:
            continue
        lo, hi = parsed
        if lo <= ss_sum <= hi:
            return (ss, row.get("percentile", "<1"))
        dist = min(abs(ss_sum - lo), abs(ss_sum - hi))
        if dist < best_dist:
            best_dist = dist
            best_abc = (ss, row.get("percentile", "<1"))
    return best_abc or (None, None)

norms.sum_ss_to_abc = _safe_sum_ss_to_abc


class ScoringService:
    """
    Authoritative service wrapper around Pearson VABS-3 normative scoring engine
    and ASD Pattern Engine.
    """

    @classmethod
    def calculate_assessment(
        cls,
        patient_info: Dict[str, Any],
        raw_scores: Dict[str, Any],
        item_responses: Dict[str, Any] = None,
        maladaptive: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Executes deterministic VABS-3 scoring and ASD pattern recognition.
        """
        item_responses = item_responses or {}
        maladaptive = maladaptive or {}

        # Run official scoring engine
        scores_result = scoring.calculate_scores(
            raw_scores=raw_scores,
            patient_info=patient_info,
            item_responses=item_responses,
            maladaptive=maladaptive,
        )

        # Run ASD Pattern Engine with safe numeric normalization
        flat = scores_result.get("flat", {})
        scores_for_patterns = {
            "com_ss": flat.get("com_ss") if flat.get("com_ss") is not None else 100,
            "dls_ss": flat.get("dls_ss") if flat.get("dls_ss") is not None else 100,
            "soc_ss": flat.get("soc_ss") if flat.get("soc_ss") is not None else 100,
            "mot_ss": flat.get("mot_ss") if flat.get("mot_ss") is not None else 100,
            "abc": flat.get("abc") if flat.get("abc") is not None else 100,
        }

        resolved_items = dict(scores_result.get("resolved_items", {}))
        mal_res = scores_result.get("maladaptive", {})
        if mal_res.get("provided") and mal_res.get("critical_scores"):
            resolved_items["critical"] = mal_res["critical_scores"]

        patterns_result = pattern_engine.analyze_asd_patterns(
            scores=scores_for_patterns,
            item_responses=resolved_items or None,
        )

        clinical_safeguard = (
            "Autism Lens provides decision support and descriptive adaptive behavior analysis. "
            "It does NOT constitute an automated definitive diagnosis. All findings require review "
            "and integration with direct clinical observation, developmental history, and countersignature "
            "by a qualified healthcare professional."
        )

        return {
            "ok": True,
            "patient_info": patient_info,
            "scores": scores_result,
            "patterns": patterns_result,
            "scoring_source": scoring.SCORING_SOURCE,
            "clinical_safeguard": clinical_safeguard,
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Returns domains, subdomains, and item metadata for frontend forms."""
        subs = {}
        for code in meta.SUBDOMAINS:
            subs[code] = item_defs.item_meta(code)

        maladaptive = {
            "int": [{"num": i + 1, "desc": d} for i, d in enumerate(item_defs.INTERNALIZING)],
            "ext": [{"num": i + 1, "desc": d} for i, d in enumerate(item_defs.EXTERNALIZING)],
            "critical": [
                {"num": i + 1, "desc": d, "urgent": (i + 1) in item_defs.URGENT_CRITICAL}
                for i, d in enumerate(item_defs.CRITICAL)
            ],
        }

        return {
            "domains": meta.DOMAINS,
            "subdomains": meta.SUBDOMAINS,
            "maladaptive": meta.MALADAPTIVE,
            "age_markers": age_markers.AGE_MARKERS,
            "item_data": {
                "subdomains": subs,
                "maladaptive": maladaptive,
            },
        }
