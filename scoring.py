# -*- coding: utf-8 -*-
"""
scoring.py
==========
Vineland-3 (VABS-3) scoring pipeline - now powered by the LICENSED Pearson
normative tables in norms.py (Appendix B.1/B.3).
"""

import math
import meta
import age_markers
import items as item_defs
import norms

SCORING_SOURCE = "official Pearson VABS-3 normative tables"

def calculate_raw_score(item_scores, age_start_item=1):
    """
    Raw Score = Box C + Box D
    """
    n = len(item_scores)
    scores = [(int(s) if s in (0, 1, 2, '0', '1', '2') else -1) for s in item_scores]

    age_passed = []
    age_start_item = max(1, min(int(age_start_item or 1), n))
    for i in range(age_start_item - 1):
        age_passed.append(i)
        if scores[i] == -1:
            scores[i] = 2

    basal_item = 1
    basal_found = False
    for i in range(n - 3):
        if scores[i] == 2 and scores[i+1] == 2 and scores[i+2] == 2 and scores[i+3] == 2:
            basal_item = i + 4
            basal_found = True

    ceiling_start = n
    ceiling_end = n
    ceiling_found = False
    for i in range(basal_item, n - 3):
        if scores[i] == 0 and scores[i+1] == 0 and scores[i+2] == 0 and scores[i+3] == 0:
            ceiling_start = i + 1
            ceiling_end = i + 4
            ceiling_found = True
            break

    box_c = basal_item * 2
    box_d = 0
    for i in range(basal_item, ceiling_start - 1):
        s = scores[i]
        if s in (0, 1, 2):
            box_d += s

    raw_score = box_c + box_d
    return {
        'basal_item': basal_item,
        'basal_found': basal_found,
        'ceiling_start': ceiling_start,
        'ceiling_end': ceiling_end,
        'ceiling_item': ceiling_start,
        'ceiling_found': ceiling_found,
        'box_c': box_c,
        'box_d': box_d,
        'raw_score': raw_score,
        'basal_passed': list(range(0, basal_item - 1)),
        'ceiling_failed': list(range(ceiling_end, n)),
        'age_passed': age_passed,
    }

def _resolved_from_calc(item_scores, calc):
    """Effective 0/1/2 array (<=basal->2, >=ceiling_start->0) for patterns."""
    n = len(item_scores)
    basal_item = calc['basal_item']
    ceiling_start = calc['ceiling_start']
    out = []
    for idx in range(n):
        num = idx + 1
        if num <= basal_item:
            out.append(2)
        elif num >= ceiling_start:
            out.append(0)
        else:
            s = item_scores[idx]
            out.append(s if s in (0, 1, 2) else 0)
    return out

def _confidence_intervals(ss, domain):
    out = {}
    for level_key, level in (('85', 0.85), ('90', 0.9), ('95', 0.95)):
        lo, hi = norms.get_confidence_interval(ss, domain, level)
        out[level_key] = {'low': lo, 'high': hi, 'text': '{} - {}'.format(lo, hi)}
    return out

def _base_rate(diff, sd):
    z = abs(diff) / sd
    p = 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))
    return '{}%'.format(max(1, min(99, round(p * 100))))

def _flat_keys(subdomains, domains, composite, sw_summary):
    flat = {}
    for code, s in subdomains.items():
        flat['{}_v'.format(code)] = s['v']
    for dcode, d in domains.items():
        flat['{}_ss'.format(dcode.lower())] = d['ss']
        flat['{}_band'.format(dcode.lower())] = d['band']
    flat['abc'] = composite['abc']
    flat['abc_band'] = composite['abc_band']
    flat['strength_weakness'] = sw_summary
    return flat

def _to_int(value, default=0):
    try:
        if value is None or value == '':
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default

def _score_maladaptive(maladaptive):
    if not maladaptive:
        return {'provided': False}

    def raw_of(key, n):
        arr = maladative.get(key, []) or [] if 'maladative' in locals() else maladaptive.get(key, []) or []
        vals = [(v if v in (0, 1, 2) else 0) for v in arr][:n]
        return sum(vals), vals

    int_raw, int_scores = raw_of('int', 13)
    ext_raw, ext_scores = raw_of('ext', 11)
    crit_raw, crit_scores = raw_of('critical', 20)

    provided = bool(int_scores or ext_scores or crit_scores)
    if not provided:
        return {'provided': False}

    int_band = meta.maladaptive_band(int_raw)
    ext_band = meta.maladaptive_band(ext_raw)

    critical_flags = []
    for idx, s in enumerate(crit_scores):
        if s in (1, 2):
            num = idx + 1
            desc = item_defs.CRITICAL[idx] if idx < len(item_defs.CRITICAL) else f"Item {num}"
            urgent = num in item_defs.URGENT_CRITICAL
            critical_flags.append({
                'num': num,
                'desc': desc,
                'score': s,
                'label': 'Often' if s == 2 else 'Sometimes',
                'urgent': urgent,
            })

    return {
        'provided': True,
        'int_raw': int_raw,
        'int_band': int_band,
        'int_color': meta.band_color(int_band),
        'ext_raw': ext_raw,
        'ext_band': ext_band,
        'ext_color': meta.band_color(ext_band),
        'critical_count': len(critical_flags),
        'critical_flags': critical_flags,
        'critical_scores': crit_scores,
    }

def calculate_scores(raw_scores, patient_info, item_responses=None, maladaptive=None):
    age_years = _to_int(patient_info.get('age_years'), 0)
    age_months = _to_int(patient_info.get('age_months'), 0)

    subdomains = {}
    resolved_items = {}

    for code, m in meta.SUBDOMAINS.items():
        sub_max = meta.max_raw(code)
        from_items = False
        calc = None

        if item_responses and code in item_responses and isinstance(item_responses[code], list) and len(item_responses[code]) > 0:
            item_scores = item_responses[code]
            start_marker = age_markers.get_recommended_start_item(code, age_years)
            age_start_item = start_marker.get('start_item', 1)
            calc = calculate_raw_score(item_scores, age_start_item)
            raw = calc['raw_score']
            from_items = True
            resolved_items[code] = _resolved_from_calc(item_scores, calc)
        else:
            raw = _to_int(raw_scores.get(code), 0)

        raw_for_v = max(0, min(raw, sub_max))
        v, age_key = norms.raw_to_v_scale(code, raw_for_v, age_years, age_months)
        ae_b2 = norms.raw_to_age_equivalent(code, raw_for_v)
        gsv = norms.raw_to_gsv(code, raw_for_v)
        band = meta.vscale_band_label(v)

        sd = {
            'code': code,
            'name': m['name'],
            'domain': m['domain'],
            'items': m['items'],
            'max_raw': sub_max,
            'raw': raw,
            'v': v,
            'v_scale': v,
            'v_band': band,
            'band': band,
            'age_equiv': ae_b2 if ae_b2 is not None else meta.age_equiv(code, raw),
            'gsv': gsv if gsv is not None else '-',
            'pct_est': '-',
            'age_key': age_key,
            'from_items': from_items,
        }

        if calc:
            sd.update({
                'basal_item': calc['basal_item'],
                'basal_found': calc['basal_found'],
                'ceiling_item': calc['ceiling_start'],
                'ceiling_found': calc['ceiling_found'],
                'ceiling_start': calc['ceiling_start'],
                'ceiling_end': calc['ceiling_end'],
                'box_c': calc['box_c'],
                'box_d': calc['box_d'],
                'auto_filled_below': calc['basal_passed'],
                'auto_filled_above': calc['ceiling_failed'],
                'age_start_item': age_start_item,
                'age_passed': calc['age_passed'],
            })

        subdomains[code] = sd

    domains = {}
    for dcode, dmeta in meta.DOMAINS.items():
        subs = [subdomains[sc] for sc in dmeta['subs']]
        vsum = sum(s['v'] for s in subs if s['v'] is not None)
        ss, pct = norms.v_sum_to_standard_score(dcode.lower(), vsum, age_years, age_months)
        band = norms.get_normative_band(ss)
        domains[dcode] = {
            'code': dcode,
            'name': dmeta['name'],
            'color': dmeta['color'],
            'subs': subs,
            'v_sum': vsum,
            'ss': ss,
            'band': band,
            'band_color': meta.band_color(band),
            'percentile': pct if pct is not None else '-',
            'ci': _confidence_intervals(ss, dcode.lower()) if ss is not None else {},
        }

    com_ss = domains['COM']['ss']
    dls_ss = domains['DLS']['ss']
    soc_ss = domains['SOC']['ss']

    if com_ss is not None and dls_ss is not None and soc_ss is not None:
        abc_sum = com_ss + dls_ss + soc_ss
        abc, abc_pct = norms.sum_ss_to_abc(abc_sum, age_years, age_months)
        abc_band = norms.get_normative_band(abc)
        composite = {
            'abc': abc,
            'abc_sum': abc_sum,
            'abc_band': abc_band,
            'abc_band_color': meta.band_color(abc_band),
            'percentile': abc_pct if abc_pct is not None else '-',
            'ci': _confidence_intervals(abc, 'abc') if abc is not None else {},
        }
    else:
        composite = {
            'abc': None,
            'abc_sum': None,
            'abc_band': 'Unknown',
            'abc_band_color': '#555555',
            'percentile': '-',
            'ci': {},
        }

    domain_order = ['COM', 'DLS', 'SOC', 'MOT']
    all_ss = [domains[d]['ss'] for d in domain_order if domains[d]['ss'] is not None]
    mean_ss = round(sum(all_ss) / len(all_ss)) if all_ss else 100

    strength_weakness = []
    for dcode in domain_order:
        d = domains[dcode]
        if d['ss'] is not None:
            diff = d['ss'] - mean_ss
            if diff >= 10:
                verdict = 'Strength'
            elif diff <= -10:
                verdict = 'Weakness'
            else:
                verdict = 'Within Normal Limits'
            strength_weakness.append({
                'domain': dcode,
                'name': d['name'],
                'ss': d['ss'],
                'mean_ss': mean_ss,
                'diff': diff,
                'verdict': verdict,
                'base_rate': _base_rate(diff, 10),
            })

    pairwise = []
    for i in range(len(domain_order)):
        for j in range(i + 1, len(domain_order)):
            d1 = domains[domain_order[i]]
            d2 = domains[domain_order[j]]
            if d1['ss'] is not None and d2['ss'] is not None:
                diff = d1['ss'] - d2['ss']
                abs_diff = abs(diff)
                significant = 'Yes' if abs_diff >= 15 else 'No'
                pairwise.append({
                    'd1': d1['code'],
                    'd1_name': d1['name'],
                    'ss1': d1['ss'],
                    'd2': d2['code'],
                    'd2_name': d2['name'],
                    'ss2': d2['ss'],
                    'diff': diff,
                    'abs_diff': abs_diff,
                    'significant': significant,
                    'base_rate': _base_rate(diff, 12),
                })

    sw_summary = '; '.join(f"{item['domain']} {item['verdict']} ({item['diff']:+d})" for item in strength_weakness if item['verdict'] != 'Within Normal Limits')
    maladaptive_result = _score_maladaptive(maladaptive)

    flat = _flat_keys(subdomains, domains, composite, sw_summary)
    flat['mean_ss'] = mean_ss

    return {
        'patient_info': patient_info,
        'age_text': f"{age_years}y {age_months}m",
        'subdomains': subdomains,
        'domains': domains,
        'composite': composite,
        'strength_weakness': strength_weakness,
        'pairwise': pairwise,
        'mean_ss': mean_ss,
        'scoring_source': SCORING_SOURCE,
        'maladaptive': maladaptive_result,
        'resolved_items': resolved_items,
        'flat': flat,
    }
