# -*- coding: utf-8 -*-
"""
pattern_engine.py
=================
Identifies ASD-related adaptive behavior patterns from VABS-3 scores and items.

Clinical basis:
  - DSM-5-TR ASD criteria (Criterion A: social-communication deficits;
    Criterion B: restricted/repetitive behaviors).
  - VABS-3 manual ASD research (p.73): Socialization most impaired, then
    Communication, with Daily Living relatively preserved and Motor typically
    within normal limits; ABC usually 1.5-2.5 SD below the mean; greater
    subdomain scatter than other clinical groups.

DEMO SYSTEM - descriptive, NOT diagnostic. Not for clinical use.
"""

def analyze_asd_patterns(scores, item_responses=None):
    patterns = []
    flags = []

    com_ss = scores.get('com_ss', 100)
    dls_ss = scores.get('dls_ss', 100)
    soc_ss = scores.get('soc_ss', 100)
    mot_ss = scores.get('mot_ss', 100)
    abc = scores.get('abc', 100)

    # 1. Classic ASD
    if soc_ss < com_ss < dls_ss and mot_ss >= 85:
        patterns.append({
            'name': 'Classic ASD Adaptive Profile',
            'description': (
                'Socialization most impaired, Communication second, Daily Living '
                'relatively preserved, Motor adequate. This domain ordering is the '
                'hallmark adaptive profile in Autism Spectrum Disorder (VABS-3 manual, '
                'p.73). Consistent with DSM-5-TR Criteria A and B.'
            ),
            'severity': 'high',
            'dsm_link': 'DSM-5-TR Criterion A (social communication deficits)',
        })

    # 2. High-Functioning ASD
    if soc_ss < com_ss and abs(com_ss - dls_ss) <= 10 and 70 <= abc <= 95:
        patterns.append({
            'name': 'High-Functioning ASD Adaptive Profile',
            'description': (
                'Socialization most impaired with Communication and Daily Living '
                'relatively closer together. ABC in the borderline-adequate range. '
                'Pattern consistent with higher-functioning ASD or ASD Level 1 (requiring support).'
            ),
            'severity': 'medium',
            'dsm_link': 'ASD Level 1 - Requiring Support',
        })

    # 3. Severe ASD
    if abc < 70 and soc_ss < 70 and com_ss < 70:
        patterns.append({
            'name': 'Severe ASD Adaptive Profile',
            'description': (
                'All core domains significantly impaired with Socialization and '
                'Communication most severely affected. ABC below 70 indicates a global '
                'adaptive deficit. Consistent with ASD Level 2-3 (requiring substantial support).'
            ),
            'severity': 'high',
            'dsm_link': 'ASD Level 2-3 - Requiring Substantial/Very Substantial Support',
        })

    # 4. Social-Communication Co-Deficit
    if com_ss < 85 and soc_ss < 85 and abs(com_ss - soc_ss) < 12:
        patterns.append({
            'name': 'Social-Communication Co-Deficit',
            'description': (
                'Both Communication and Socialization are similarly impaired. This '
                'co-occurrence reflects the unified DSM-5-TR Criterion A construct of '
                'social communication deficit.'
            ),
            'severity': 'high',
            'dsm_link': 'DSM-5-TR Criterion A - Social Communication Deficits',
        })

    # 5. Motor Preservation
    if mot_ss >= 90 and soc_ss < 80 and com_ss < 80:
        patterns.append({
            'name': 'Motor Preservation with Social-Communication Deficit',
            'description': (
                'Motor skills within normal limits while social-communication is '
                'significantly impaired. This dissociation is clinically characteristic '
                'of ASD and distinguishes it from global developmental delay.'
            ),
            'severity': 'medium',
            'dsm_link': 'ASD associated feature: motor skills relatively preserved',
        })

    # 6. Atypical Profile
    if dls_ss < soc_ss and dls_ss < 75:
        patterns.append({
            'name': 'Atypical Profile - Daily Living Below Socialization',
            'description': (
                'Daily Living Skills are more impaired than Socialization. This is atypical '
                'for ASD and may suggest comorbid intellectual disability or a non-ASD primary presentation.'
            ),
            'severity': 'medium',
            'dsm_link': 'Consider comorbid intellectual disability (DSM-5-TR)',
        })

    # 7. Significant Skill Imbalance
    all_ss = [com_ss, dls_ss, soc_ss, mot_ss]
    score_range = max(all_ss) - min(all_ss)
    if score_range >= 25:
        patterns.append({
            'name': 'Significant Skill Imbalance',
            'description': (
                f'{score_range}-point range across domains indicates uneven adaptive '
                'skill development - greater scatter than typically observed in the general '
                'population. Elevated subdomain scatter is characteristic of ASD.'
            ),
            'severity': 'medium',
            'dsm_link': 'ASD feature: uneven developmental profile',
        })

    # 8. Global Adaptive Behavior Deficit
    if abc < 70:
        patterns.append({
            'name': 'Global Adaptive Behavior Deficit',
            'description': (
                'ABC below 70 (>2 SD below mean) indicates significant impairment across '
                'adaptive domains. May reflect ASD with intellectual disability, severe ASD, or both.'
            ),
            'severity': 'high',
            'dsm_link': 'DSM-5-TR: ASD with intellectual impairment specifier',
        })

    # Item-level flags
    if item_responses:
        ipr_items = item_responses.get('ipr', [])
        if sum(1 for s in ipr_items[:10] if s == 0) >= 5:
            flags.append({
                'text': (
                    'Failure on basic social initiation items (ipr 1-10) - suggests '
                    'early-emerging social deficit consistent with DSM-5-TR Criterion A1 '
                    '(social-emotional reciprocity).'
                ),
                'severity': 'high',
            })

        rec_items = item_responses.get('rec', [])
        if sum(1 for s in rec_items[:15] if s == 0) >= 6:
            flags.append({
                'text': (
                    'Failure on basic receptive language items (rec 1-15) - suggests '
                    'language comprehension deficit consistent with DSM-5-TR Criterion A2.'
                ),
                'severity': 'high',
            })

        cop_items = item_responses.get('cop', [])
        if len(cop_items) > 6 and cop_items[3] == 0 and cop_items[6] == 0:
            flags.append({
                'text': (
                    'Difficulty with transitions and routine changes (cop items 4, 7) - '
                    'consistent with DSM-5-TR Criterion B2 (insistence on sameness).'
                ),
                'severity': 'medium',
            })

        pla_items = item_responses.get('pla', [])
        if len(pla_items) > 11 and sum(1 for s in pla_items[6:12] if s == 0) >= 4:
            flags.append({
                'text': (
                    'Significant peer play deficits (pla 7-12) - consistent with DSM-5-TR '
                    'Criterion A3 (deficits in developing peer relationships).'
                ),
                'severity': 'high',
            })

        critical_items = item_responses.get('critical', [])
        asd_critical = [0, 3, 5, 8]
        critical_flags = [i + 1 for i in asd_critical if i < len(critical_items) and critical_items[i] >= 1]
        if critical_flags:
            flags.append({
                'text': (
                    f'Critical Items {critical_flags} endorsed - fixation on objects, '
                    'repetitive speech, repetitive movements, or compulsive behaviors present. '
                    'Consistent with DSM-5-TR Criteria B1 and B2.'
                ),
                'severity': 'high',
            })

    likelihood = _calculate_profile_likelihood(patterns)
    return {
        'patterns': patterns,
        'flags': flags,
        'asd_profile_likelihood': likelihood,
        'score_range': score_range,
    }

def _calculate_profile_likelihood(patterns):
    high = sum(1 for p in patterns if p['severity'] == 'high')
    med = sum(1 for p in patterns if p['severity'] == 'medium')
    if high >= 2:
        return {
            'label': 'Strongly Consistent with ASD-Related Adaptive Profile',
            'color': 'danger',
            'description': (
                'Multiple high-severity ASD-characteristic patterns identified. '
                'The adaptive behavior profile is strongly consistent with patterns '
                'documented in ASD research. Comprehensive diagnostic evaluation strongly recommended.'
            ),
        }
    elif high == 1 or med >= 2:
        return {
            'label': 'Partially Consistent with ASD-Related Adaptive Profile',
            'color': 'warning',
            'description': (
                'Some ASD-characteristic patterns identified. The profile shares '
                'features with ASD-related adaptive functioning but is not conclusive. '
                'Further evaluation recommended.'
            ),
        }
    else:
        return {
            'label': 'Insufficient Evidence for ASD-Specific Profile',
            'color': 'info',
            'description': (
                'Current data does not show a clear ASD-characteristic adaptive behavior '
                'profile. This does not rule out ASD - clinical observation and additional '
                'assessment are required.'
            ),
        }
