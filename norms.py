# -*- coding: utf-8 -*-
"""
norms.py -- VABS-3 Normative Lookup Tables
Source: Vineland Adaptive Behavior Scales, Third Edition
        Appendix B: Comprehensive Interview Form Norms Tables
        (c) 2016 NCS Pearson, Inc. All rights reserved.
Used under departmental license for academic research purposes.
"""

from norms_tables import TABLE_B1, TABLE_B2, TABLE_B3

def get_age_key_b1(age_years, age_months):
    """
    Returns the correct B.1 age group key for a given age.
    B.1 age groups are in 2-month intervals for ages 3-4,
    3-month intervals for ages 5-9.
    """
    total_months = age_years * 12 + age_months
    if 36 <= total_months <= 59:
        start = (total_months // 2) * 2
        end = start + 1
        sy, sm = divmod(start, 12)
        ey, em = divmod(end, 12)
        return f"{sy}:{sm}-{ey}:{em}"
    elif 60 <= total_months <= 119:
        group_start = (total_months // 3) * 3
        group_end = group_start + 2
        sy, sm = divmod(group_start, 12)
        ey, em = divmod(group_end, 12)
        return f"{sy}:{sm}-{ey}:{em}"
    return None

def get_age_key_b3(age_years, age_months):
    """
    Returns the correct B.3 age group key for a given age.
    """
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
    if 72 <= total_months <= 83:
        return "6:0-6:11"
    if 84 <= total_months <= 95:
        return "7:0-7:11"
    if 96 <= total_months <= 107:
        return "8:0-8:11"
    if 108 <= total_months <= 119:
        return "9:0-9:11"
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
    if 204 <= total_months <= 215:
        return "17:0-17:11"
    if 216 <= total_months <= 227:
        return "18:0-18:11"
    if 228 <= total_months <= 239:
        return "19:0-19:11"
    if 240 <= total_months <= 299:
        return "20:0-24:11"
    if 300 <= total_months <= 359:
        return "25:0-29:11"
    if 360 <= total_months <= 479:
        return "30:0-39:11"
    if 480 <= total_months <= 599:
        return "40:0-49:11"
    if 600 <= total_months <= 719:
        return "50:0-59:11"
    if 720 <= total_months <= 839:
        return "60:0-69:11"
    return "70-90+"

def parse_range(val):
    """Parse a value like '36-38' or '72' or em-dash into (min, max) or None."""
    if val in ("\u2014", "\u2013", "-", "--") or val is None:
        return None
    val = str(val).strip()
    if "-" in val:
        parts = val.split("-")
        try:
            return (int(parts[0]), int(parts[1]))
        except:
            return None
    try:
        v = int(val)
        return (v, v)
    except:
        return None

def raw_to_v_scale(subdomain, raw_score, age_years, age_months):
    """
    Convert a raw score to a v-scale score using Table B.1.
    Returns (v_scale, age_key) or (None, None) if not found.
    """
    age_key = get_age_key_b1(age_years, age_months)
    if not age_key or age_key not in TABLE_B1:
        age_key = _find_closest_b1_key(age_years, age_months)
    if not age_key:
        return (None, None)

    age_table = TABLE_B1[age_key]
    for vs in range(1, 25):
        vs_str = str(vs)
        if vs_str not in age_table:
            continue
        row = age_table[vs_str]
        sd_range = row.get(subdomain, "\u2014")
        parsed = parse_range(sd_range)
        if parsed is None:
            continue
        lo, hi = parsed
        if lo <= raw_score <= hi:
            return (vs, age_key)

    max_val = -1
    for vs in range(1, 25):
        vs_str = str(vs)
        if vs_str not in age_table:
            continue
        row = age_table[vs_str]
        sd_range = row.get(subdomain, "\u2014")
        parsed = parse_range(sd_range)
        if parsed:
            lo, hi = parsed
            if raw_score > hi:
                max_val = max(max_val, vs)
    if max_val > 0:
        return (24, age_key)
    return (1, age_key)

def _find_closest_b1_key(age_years, age_months):
    """Find closest available B.1 key if exact match not found."""
    total_months = age_years * 12 + age_months
    keys = list(TABLE_B1.keys())

    def key_to_months(key):
        try:
            parts = key.split("-")
            y, m = parts[0].split(":")
            return int(y) * 12 + int(m)
        except:
            return 9999

    closest = min(keys, key=lambda k: abs(key_to_months(k) - total_months))
    return closest

def v_sum_to_standard_score(domain, v_sum, age_years, age_months):
    """
    Convert sum of v-scales to a domain standard score using Table B.3.
    domain: 'com', 'dls', 'soc', 'mot'
    v_sum: integer sum of v-scale scores for that domain
    Returns (standard_score, percentile) or (None, None)
    """
    age_key = get_age_key_b3(age_years, age_months)
    if not age_key or age_key not in TABLE_B3:
        return (None, None)

    domain_col = {
        'com': 'com_sum',
        'dls': 'dls_sum',
        'soc': 'soc_sum',
        'mot': 'mot_sum',
    }.get(domain.lower())

    if not domain_col:
        return (None, None)

    age_table = TABLE_B3[age_key]
    best_ss = None
    best_dist = float("inf")

    for ss_str, row in age_table.items():
        ss = int(ss_str)
        col_val = row.get(domain_col, "\u2014")
        parsed = parse_range(col_val)
        if parsed is None:
            continue
        lo, hi = parsed
        if lo <= v_sum <= hi:
            return (ss, row.get("percentile", "<1"))
        dist = min(abs(v_sum - lo), abs(v_sum - hi))
        if dist < best_dist:
            best_dist = dist
            best_ss = (ss, row.get("percentile", "<1"))

    if best_ss:
        return best_ss
    return (None, None)

def sum_ss_to_abc(ss_sum, age_years, age_months):
    """
    Convert sum of domain standard scores (COM+DLS+SOC) to ABC
    using Table B.3.
    Returns (abc, percentile) or (None, None)
    """
    age_key = get_age_key_b3(age_years, age_months)
    if not age_key or age_key not in TABLE_B3:
        return (None, None)

    age_table = TABLE_B3[age_key]
    best_abc = None
    best_dist = float("inf")

    for ss_str, row in age_table.items():
        ss = int(ss_str)
        abc_val = row.get("abc_sum", "\u2014")
        parsed = parse_range(abc_val)
        if parsed is None:
            continue
        lo, hi = parsed
        if lo <= ss_sum <= hi:
            return (ss, row.get("percentile", "<1"))
        dist = min(abs(ss_sum - lo), abs(ss_sum - hi))
        if dist < best_dist:
            best_dist = dist
            best_abc = (ss, row.get("percentile", "<1"))

    if best_abc:
        return best_abc
    return (None, None)

def get_normative_band(ss):
    """Return the normative band label for a standard score."""
    if ss is None:
        return "Unknown"
    if ss < 70:
        return "Low"
    if ss <= 79:
        return "Moderately Low"
    if ss <= 89:
        return "Adequate \u2014 Below Average"
    if ss <= 110:
        return "Adequate"
    if ss <= 120:
        return "Adequate \u2014 Above Average"
    if ss <= 130:
        return "High"
    return "Very High"

def get_confidence_interval(ss, domain, level=0.9):
    """
    Return the confidence interval for a standard score using domain-specific
    SEMs (VABS-3 average standard errors of measurement).
    """
    sem_by_domain = {
        'com': 3.7, 'dls': 3.7, 'soc': 3.7, 'abc': 2.5, 'mot': 4.9
    }
    sem = sem_by_domain.get(domain.lower(), 3.7)
    z = {0.85: 1.44, 0.9: 1.65, 0.95: 1.96}.get(level, 1.65)
    margin = round(z * sem)
    return (ss - margin, ss + margin)

def raw_to_gsv(subdomain, raw_score):
    """Growth Scale Value for a subdomain raw score (Table B.2)."""
    cell = TABLE_B2.get(subdomain, {}).get(int(raw_score))
    if cell:
        return cell[1]
    return None

def raw_to_age_equivalent(subdomain, raw_score):
    """Age Equivalent (e.g. '2:5', '<3:0') for a raw score (Table B.2)."""
    cell = TABLE_B2.get(subdomain, {}).get(int(raw_score))
    if cell:
        return cell[0]
    return None
