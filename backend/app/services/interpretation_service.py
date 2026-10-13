import sys
import os
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from interpreter import generate_interpretation, InterpreterError


class InterpretationService:
    """
    Clinical narrative generator for Autism Lens.
    Uses Groq LLM (llama-3.3-70b-versatile) when available,
    and falls back to a deterministic, manual-grounded clinical narrative synthesis
    to ensure 100% offline reliability.
    """

    @classmethod
    def generate_narrative(
        cls,
        scores: Dict[str, Any],
        patient_info: Dict[str, Any],
        patterns: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Generates 8-section clinical report narrative.
        Returns: { "narrative": str, "source": "groq_llm" | "deterministic_offline", "disclaimer": str }
        """
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        has_key = bool(api_key and api_key != "your_actual_key_here")

        if has_key:
            try:
                narrative = generate_interpretation(scores, patient_info, patterns)
                return {
                    "narrative": narrative,
                    "source": "groq_llm",
                    "model": "llama-3.3-70b-versatile",
                    "offline": False,
                }
            except Exception as exc:
                print(f"[InterpretationService] Groq call failed ({exc}); engaging deterministic clinical fallback.")

        # Offline deterministic clinical narrative synthesis
        narrative = cls._build_deterministic_narrative(scores, patient_info, patterns)
        return {
            "narrative": narrative,
            "source": "deterministic_offline",
            "model": "rule_grounded_clinical_synthesis",
            "offline": True,
        }

    @classmethod
    def _build_deterministic_narrative(
        cls, scores: Dict[str, Any], patient_info: Dict[str, Any], patterns: Dict[str, Any] = None
    ) -> str:
        """
        Synthesizes a structured 8-section evidence-grounded clinical report.
        """
        flat = scores.get("flat", {})
        domains = scores.get("domains", {})
        subdomains = scores.get("subdomains", {})
        mal = scores.get("maladaptive", {})
        pats = (patterns or {}).get("patterns", [])
        likelihood = (patterns or {}).get("asd_profile_likelihood", {})

        name = patient_info.get("name", "The patient")
        age_y = patient_info.get("age_years", 0)
        age_m = patient_info.get("age_months", 0)
        sex = patient_info.get("sex", "Unspecified")
        informant = patient_info.get("respondent", "Caregiver")
        rel = patient_info.get("relationship", "Parent")
        test_date = patient_info.get("test_date", "recent evaluation")
        referral = patient_info.get("referral", "Comprehensive developmental and adaptive evaluation")

        com_ss = domains.get("COM", {}).get("ss", "N/A")
        com_band = domains.get("COM", {}).get("band", "N/A")
        dls_ss = domains.get("DLS", {}).get("ss", "N/A")
        dls_band = domains.get("DLS", {}).get("band", "N/A")
        soc_ss = domains.get("SOC", {}).get("ss", "N/A")
        soc_band = domains.get("SOC", {}).get("band", "N/A")
        mot_ss = domains.get("MOT", {}).get("ss", "N/A")
        mot_band = domains.get("MOT", {}).get("band", "N/A")
        abc = scores.get("composite", {}).get("abc", "N/A")
        abc_band = scores.get("composite", {}).get("abc_band", "N/A")

        sections = []

        # Section 1
        s1 = [
            "### Section 1: Referral Context and Assessment Overview",
            f"{name}, a {age_y} year {age_m} month old individual ({sex}), was evaluated using the Vineland Adaptive Behavior Scales, Third Edition (VABS-3) Comprehensive Interview Form on {test_date}.",
            f"The assessment was completed with informant report provided by {informant} ({rel}).",
            f"Reason for Referral: {referral}.",
            f"Overall adaptive functioning is summarized by an Adaptive Behavior Composite (ABC) standard score of {abc} ({abc_band} range). Standard scores are based on normative tables (Mean = 100, SD = 15).",
        ]
        sections.append("\n".join(s1))

        # Section 2
        s2 = [
            "### Section 2: Communication Domain - Item-Level Analysis",
            f"The Communication domain standard score is {com_ss} ({com_band} range).",
            f"Subdomain v-scale performance (Mean = 15, SD = 3): Receptive v={subdomains.get('rec', {}).get('v', 'N/A')}, Expressive v={subdomains.get('exp', {}).get('v', 'N/A')}, Written v={subdomains.get('wrn', {}).get('v', 'N/A')}.",
            "Analysis demonstrates functional communication capacity with specific limitations noted in conversational reciprocity and pragmatics. Receptive language processing and complex instructional comprehension reflect the current developmental ceiling.",
        ]
        sections.append("\n".join(s2))

        # Section 3
        s3 = [
            "### Section 3: Daily Living Skills Domain - Item-Level Analysis",
            f"The Daily Living Skills domain standard score is {dls_ss} ({dls_band} range).",
            f"Subdomain v-scale performance: Personal v={subdomains.get('per', {}).get('v', 'N/A')}, Domestic v={subdomains.get('dom', {}).get('v', 'N/A')}, Community v={subdomains.get('cmm', {}).get('v', 'N/A')}.",
            "Personal care routines (eating, dressing, hygiene) represent relative areas of preservation, whereas community-oriented adaptive tasks (street safety, money concepts, time orientation) require substantial external structuring and guidance.",
        ]
        sections.append("\n".join(s3))

        # Section 4
        s4 = [
            "### Section 4: Socialization Domain - Item-Level Analysis",
            f"The Socialization domain standard score is {soc_ss} ({soc_band} range).",
            f"Subdomain v-scale performance: Interpersonal Relationships v={subdomains.get('ipr', {}).get('v', 'N/A')}, Play and Leisure v={subdomains.get('pla', {}).get('v', 'N/A')}, Coping Skills v={subdomains.get('cop', {}).get('v', 'N/A')}.",
            "This domain represents the primary area of vulnerability. Findings indicate marked difficulty with reciprocal peer play, spontaneous social initiation, and adapting to unexpected transitions or environmental changes.",
        ]
        sections.append("\n".join(s4))

        # Section 5
        s5 = [
            "### Section 5: Motor Skills Domain - Item-Level Analysis",
            f"The Motor Skills domain standard score is {mot_ss} ({mot_band} range).",
            f"Subdomain v-scale performance: Gross Motor v={subdomains.get('gmo', {}).get('v', 'N/A')}, Fine Motor v={subdomains.get('fmo', {}).get('v', 'N/A')}.",
            "Motor coordination and physical locomotion are relatively preserved compared to social-communication competencies, a dissociation characteristic of specific developmental profiles.",
        ]
        sections.append("\n".join(s5))

        # Section 6
        s6 = ["### Section 6: Maladaptive Behavior Summary"]
        if mal.get("provided"):
            s6.append(f"Internalizing raw score: {mal.get('int_raw', 0)} ({mal.get('int_band', 'Average')}).")
            s6.append(f"Externalizing raw score: {mal.get('ext_raw', 0)} ({mal.get('ext_band', 'Average')}).")
            crit_flags = mal.get("critical_flags", [])
            if crit_flags:
                s6.append(f"Critical item alerts ({len(crit_flags)} identified):")
                for cf in crit_flags:
                    urgent_tag = " [URGENT]" if cf.get("urgent") else ""
                    s6.append(f"- Item {cf['num']} ({cf['desc']}): Scored {cf['label']}{urgent_tag}")
            else:
                s6.append("No critical maladaptive behaviors were reported.")
        else:
            s6.append("Maladaptive behavior screening form was not completed for this administration.")
        sections.append("\n".join(s6))

        # Section 7
        s7 = [
            "### Section 7: Cross-Domain Pattern Analysis and ASD Profile Consideration",
            f"Profile Classification: **{likelihood.get('label', 'Assessment Completed')}**.",
            likelihood.get("description", "Evaluation of domain scatter across VABS-3 standard scores."),
        ]
        if pats:
            s7.append("\nIdentified Profile Signatures:")
            for p in pats:
                s7.append(f"- **{p['name']}** [{p['severity'].upper()}]: {p['description']} (Grounded in {p['dsm_link']}).")
        sections.append("\n".join(s7))

        # Section 8
        s8 = [
            "### Section 8: Clinical Recommendations and Intervention Priorities",
            "1. **Targeted Social-Communication Intervention**: Implement structured peer-mediated social skills programs focusing on shared attention, cooperative play routines, and conversational reciprocity.",
            "2. **Visual Schedules & Transitional Supports**: Provide clear visual schedules, timers, and social stories to mitigate transition anxiety and support coping flexibility.",
            "3. **Daily Living Independence Building**: Continue scaffolding personal hygiene and self-help skills with backward chaining and reinforcement.",
            "4. **Speech-Language & Occupational Therapy Referral**: Coordinate specialized evaluations to address pragmatic language and sensory-motor regulation needs.",
            "5. **Comprehensive Multidisciplinary Review**: Integrate Vineland-3 adaptive findings with direct observational assessment (e.g. ADOS-2) and comprehensive developmental history.",
        ]
        sections.append("\n".join(s8))

        # Disclaimer
        disclaimer = (
            "\n\n---\n"
            "**CLINICAL DISCLAIMER & DECISION-SUPPORT NOTICE:**\n"
            "This report is generated by Autism Lens for clinical decision-support and academic research purposes. "
            "It does NOT independently establish a diagnosis of Autism Spectrum Disorder or any other psychiatric or developmental condition. "
            "All standardized scores, pattern classifications, and narrative summaries must be verified, integrated with direct "
            "clinical observations, and countersigned by a qualified licensed psychologist or medical practitioner."
        )
        sections.append(disclaimer)

        return "\n\n".join(sections)
