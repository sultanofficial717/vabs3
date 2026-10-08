# -*- coding: utf-8 -*-
"""
interpreter.py
==============
Generates the clinical interpretation narrative using the Groq API
(model: llama-3.3-70b-versatile).

The system prompt encodes DSM-5-TR ASD criteria and the VABS-3 manual ASD
adaptive profile (p.73) so the model reasons from item evidence and the
pattern-engine output - not just the summary scores.

GROQ_API_KEY is read from the environment (loaded from .env). Never hard-coded.
"""

import os
import items as item_defs

MODEL = 'llama-3.3-70b-versatile'

SYSTEM_PROMPT = """You are an expert clinical neuropsychologist specializing in autism spectrum
disorder (ASD) assessment using the Vineland Adaptive Behavior Scales,
Third Edition (VABS-3).

CLINICAL KNOWLEDGE BASE - use this in every interpretation:

DSM-5-TR ASD CRITERIA:
Criterion A (social communication deficits - all three required):
  A1: Social-emotional reciprocity deficits
  A2: Nonverbal communication deficits
  A3: Relationship development deficits
Criterion B (restricted/repetitive behaviors - at least two):
  B1: Stereotyped/repetitive movements or speech
  B2: Insistence on sameness, rigid routines
  B3: Highly restricted fixated interests
  B4: Sensory hyper/hyporeactivity

VABS-3 ASD ADAPTIVE PROFILE (from manual research, p.73):
  - Socialization: most severely impaired in ASD
  - Communication: second most impaired
  - Daily Living Skills: relatively better preserved
  - Motor Skills: typically within normal limits
  - ABC typically 1.5-2.5 SD below mean in ASD
  - Greatest scatter across subdomains vs other clinical groups
  - Play/Leisure and Coping Skills particularly low
  - Critical Maladaptive Items frequently elevated

ASD PROFILE SIGNATURES:
  Classic ASD:       SOC << COM < DLS, MOT adequate, ABC < 85
  High-functioning:  SOC < COM <= DLS, MOT normal, ABC 70-90
  Severe ASD:        All domains low, SOC+COM most impaired, ABC < 70

SCORING SOURCE:
  Scores in this report are calculated from the official Pearson VABS-3
  normative tables (Appendix B, Comprehensive Interview Form). They are
  clinically accurate and may be used for interpretation purposes subject
  to qualified clinician review.

YOUR TASK - generate interpretation in 8 sections:

Section 1: Referral Context and Assessment Overview
  State patient info, instruments used, informant.

Section 2: Communication Domain - Item-Level Analysis
  - Which specific communication skills are intact, emerging, or absent
  - Explain WHY the domain score is what it is from item evidence
  - Connect to DSM-5-TR A1 (reciprocity) and A2 (nonverbal) where relevant
  - Example format: "The child demonstrates [specific skill from items scored 2]
    but consistently fails [specific skill from items scored 0], indicating that
    [functional implication]."

Section 3: Daily Living Skills Domain - Item-Level Analysis
  - Specific self-care, domestic, and community skills profile
  - Note discrepancies between Personal (usually better) and Community (usually worse)

Section 4: Socialization Domain - Item-Level Analysis
  - Specific interpersonal, play, and coping findings
  - Connect to DSM-5-TR Criterion A (social communication)
  - Note Play/Leisure and Coping Skills findings specifically

Section 5: Motor Skills Domain - Item-Level Analysis
  - Note if motor is preserved relative to other domains (ASD-relevant finding)

Section 6: Maladaptive Behavior Summary
  - If data provided: interpret Internalizing, Externalizing, Critical Items
  - Flag any Critical Items scored 1 or 2 by name
  - Connect B1/B2/B4 criterion behaviors to Critical Item findings

Section 7: Cross-Domain Pattern Analysis and ASD Profile Consideration
  - Compare all domain SS scores
  - State whether the profile matches Classic ASD, High-Functioning ASD,
    Severe ASD, or is atypical/inconclusive
  - Cite specific score evidence for the pattern identified
  - Use language: "This adaptive behavior profile is [consistent with /
    partially consistent with / not consistent with] the adaptive functioning
    patterns commonly observed in ASD, as the [specific evidence]."
  - ALWAYS state: this is descriptive, not diagnostic

Section 8: Clinical Recommendations and Intervention Priorities
  - List 4-6 specific evidence-based recommendations
  - Prioritize by domain severity
  - Include referral suggestions

MANDATORY DISCLAIMER at end:
DISCLAIMER: This report was AI-generated for research and demonstration purposes
using the VABS-3 Comprehensive Interview Form. It does not constitute a clinical
diagnosis of Autism Spectrum Disorder or any other condition. All findings must
be reviewed, integrated with direct clinical observation, developmental history,
and other assessment data, and countersigned by a licensed clinician before
any clinical or diagnostic use."""


class InterpreterError(Exception):
    """Raised when the narrative cannot be generated."""
    pass


def generate_interpretation(result, patient_info, pattern_analysis=None):
    """
    `result` is the full dict from scoring.calculate_scores().
    `pattern_analysis` is the dict from pattern_engine.analyze_asd_patterns().
    """
    api_key = os.environ.get('GROQ_API_KEY', '').strip()
    if not api_key:
        raise InterpreterError('GROQ_API_KEY is not set. Add it to the .env file in the vineland_demo folder as a line:  GROQ_API_KEY=your_key_here  (get a free key at https://console.groq.com), then restart the app.')

    try:
        from groq import Groq
    except ImportError as exc:
        raise InterpreterError("The 'groq' package is not installed. Run: pip install -r requirements.txt") from exc

    client = Groq(api_key=api_key, max_retries=4, timeout=90.0)
    user_message = _build_user_message(result, patient_info, pattern_analysis)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=2600,
            temperature=0.4,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_message},
            ]
        )
        return response.choices[0].message.content
    except Exception as exc:
        name = type(exc).__name__
        if 'Connection' in name or 'Timeout' in name or 'APIConnection' in name:
            raise InterpreterError('Could not reach the Groq API (network/connection error). Check your internet connection and, if a VPN is active, try turning it OFF and clicking Generate again. Underlying error: {}'.format(exc)) from exc
        raise InterpreterError('Groq API call failed: {}'.format(exc)) from exc


def _build_user_message(result, patient_info, pattern_analysis):
    flat = result.get('flat', {})
    subdomains = result.get('subdomains', {})
    resolved = result.get('resolved_items', {})
    mal = result.get('maladaptive', {})

    def g(k, d='N/A'):
        return flat.get(k, d)

    lines = []
    lines.append('Generate a Vineland-3 interpretation report for:\n')
    lines.append('Patient Name: {}'.format(patient_info.get('name', 'N/A')))
    lines.append('Age: {} years {} months'.format(patient_info.get('age_years', 'N/A'), patient_info.get('age_months', 'N/A')))
    lines.append('Sex: {}'.format(patient_info.get('sex', 'N/A')))
    lines.append('Test Date: {}'.format(patient_info.get('test_date', 'N/A')))
    lines.append('Respondent: {} ({})'.format(patient_info.get('respondent', 'N/A'), patient_info.get('relationship', 'N/A')))
    lines.append('Referral Reason: {}\n'.format(patient_info.get('referral', 'N/A')))

    lines.append('DOMAIN AND SUBDOMAIN SCORES:')
    lines.append('Communication (COM): SS={}, Band={}'.format(g('com_ss'), g('com_band')))
    lines.append('  Receptive v={}, Expressive v={}, Written v={}'.format(g('rec_v'), g('exp_v'), g('wrn_v')))
    lines.append('Daily Living Skills (DLS): SS={}, Band={}'.format(g('dls_ss'), g('dls_band')))
    lines.append('  Personal v={}, Domestic v={}, Community v={}'.format(g('per_v'), g('dom_v'), g('cmm_v')))
    lines.append('Socialization (SOC): SS={}, Band={}'.format(g('soc_ss'), g('soc_band')))
    lines.append('  Interpersonal v={}, Play & Leisure v={}, Coping v={}'.format(g('ipr_v'), g('pla_v'), g('cop_v')))
    lines.append('Motor Skills (MOT): SS={}, Band={}'.format(g('mot_ss'), g('mot_band')))
    lines.append('  Gross Motor v={}, Fine Motor v={}'.format(g('gmo_v'), g('fmo_v')))
    lines.append('Adaptive Behavior Composite (ABC): {} ({})'.format(g('abc'), g('abc_band')))
    lines.append('Scoring source: {}'.format(result.get('scoring_source', 'official Pearson VABS-3 normative tables')))
    lines.append('(These standard scores come from the official Pearson VABS-3 normative tables (Appendix B) and are clinically accurate.)\n')

    lines.append("STRENGTH / WEAKNESS ANALYSIS (vs child's own mean SS {}):".format(result.get('mean_ss', 'N/A')))
    for r in result.get('strength_weakness', []):
        lines.append('  {} (SS {}, diff {:+d}): {}'.format(r['name'], r['ss'], r['diff'], r['verdict']))

    lines.append('PAIRWISE DOMAIN COMPARISONS (>=15 pts = significant):')
    for p in result.get('pairwise', []):
        lines.append('  {} vs {}: diff {} - {}'.format(p['d1_name'], p['d2_name'], p['abs_diff'], 'Significant' if p['significant'] == 'Yes' else 'Not significant'))
    lines.append('')

    item_block = _item_responses_block(subdomains, resolved)
    if item_block:
        lines.append('ITEM-LEVEL RESPONSES (2=full skill, 1=emerging/partial, 0=absent):')
        lines.append(item_block)

    if mal.get('provided'):
        lines.append('\nMALADAPTIVE BEHAVIOR:')
        lines.append('  Internalizing raw={} ({})'.format(mal.get('int_raw'), mal.get('int_band')))
        lines.append('  Externalizing raw={} ({})'.format(mal.get('ext_raw'), mal.get('ext_band')))
        cf = mal.get('critical_flags', [])
        if cf:
            lines.append('  Critical Items endorsed:')
            for f in cf:
                lines.append('    Item {} ({}): {}{}'.format(f['num'], f['desc'], f['label'], ' [URGENT]' if f.get('urgent') else ''))
        else:
            lines.append('  No Critical Items endorsed.')

    if pattern_analysis:
        lines.append('\nPATTERN ENGINE ANALYSIS (DSM-5-TR + VABS-3 p.73):')
        like = pattern_analysis.get('asd_profile_likelihood', {})
        lines.append('  Overall: {}'.format(like.get('label', 'N/A')))
        for p in pattern_analysis.get('patterns', []):
            lines.append('  - [{}] {}: {} ({})'.format(p['severity'].upper(), p['name'], p['description'], p['dsm_link']))
        for fl in pattern_analysis.get('flags', []):
            lines.append('  - FLAG [{}]: {}'.format(fl['severity'].upper(), fl['text']))

    lines.append('\nUse the item-level evidence and pattern analysis above to write the 8-section report. Cite specific items by their described skill when explaining domain scores.')
    return '\n'.join(lines)


def _item_responses_block(subdomains, resolved):
    out = []
    for code, arr in resolved.items():
        sub = subdomains.get(code, {})
        if not sub.get('from_items'):
            continue
        descs = item_defs.ITEMS.get(code, [])
        out.append('\n{} [{}] (raw={}, v={}, basal item {}, ceiling item {}):'.format(sub.get('name', code), code, sub.get('raw'), sub.get('v'), sub.get('basal_item'), sub.get('ceiling_item')))
        for i, score in enumerate(arr):
            desc = descs[i] if i < len(descs) else ''
            out.append('  {}. {}: {}'.format(i + 1, desc, score))
    return '\n'.join(out)
