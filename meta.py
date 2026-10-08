"""
meta.py
=======
Structural metadata and display helpers for the Vineland-3 demo.
"""

SUBDOMAINS = {
    'rec': {'name': 'Receptive', 'domain': 'COM', 'items': 39},
    'exp': {'name': 'Expressive', 'domain': 'COM', 'items': 49},
    'wrn': {'name': 'Written', 'domain': 'COM', 'items': 38},
    'per': {'name': 'Personal', 'domain': 'DLS', 'items': 55},
    'dom': {'name': 'Domestic', 'domain': 'DLS', 'items': 30},
    'cmm': {'name': 'Community', 'domain': 'DLS', 'items': 58},
    'ipr': {'name': 'Interpersonal Relationships', 'domain': 'SOC', 'items': 43},
    'pla': {'name': 'Play and Leisure', 'domain': 'SOC', 'items': 36},
    'cop': {'name': 'Coping Skills', 'domain': 'SOC', 'items': 33},
    'gmo': {'name': 'Gross Motor', 'domain': 'MOT', 'items': 43},
    'fmo': {'name': 'Fine Motor', 'domain': 'MOT', 'items': 34},
}

DOMAINS = {
    'COM': {'name': 'Communication', 'subs': ['rec', 'exp', 'wrn'], 'color': '#1565c0'},
    'DLS': {'name': 'Daily Living Skills', 'subs': ['per', 'dom', 'cmm'], 'color': '#2e7d32'},
    'SOC': {'name': 'Socialization', 'subs': ['ipr', 'pla', 'cop'], 'color': '#6a1b9a'},
    'MOT': {'name': 'Motor Skills', 'subs': ['gmo', 'fmo'], 'color': '#ef6c00'},
}

MALADAPTIVE = {
    'int': {'name': 'Internalizing', 'items': 13},
    'ext': {'name': 'Externalizing', 'items': 11},
}

_AGE_CEILING_MONTHS = {
    'rec': 216,
    'exp': 216,
    'wrn': 216,
    'per': 216,
    'dom': 216,
    'cmm': 264,
    'ipr': 216,
    'pla': 180,
    'cop': 216,
    'gmo': 84,
    'fmo': 120,
}

def max_raw(code):
    return SUBDOMAINS[code]['items'] * 2

def band_color(label):
    if not label:
        return "#555555"
    if label == "Low":
        return "#c62828"
    if label == "Moderately Low":
        return "#ef6c00"
    if "Below Average" in label:
        return "#7cb342"
    if "Above Average" in label:
        return "#0EA5A0"
    if label == "Adequate":
        return "#2e7d32"
    if label == "Moderately High":
        return "#0EA5A0"
    if "Very High" in label:
        return "#6a1b9a"
    if label == "High":
        return "#1565c0"
    return "#555555"

def vscale_band_label(v):
    if v is None:
        return "\u2014"
    if v <= 9:
        return "Low"
    if v <= 12:
        return "Moderately Low"
    if v <= 17:
        return "Adequate"
    if v <= 20:
        return "Moderately High"
    return "High"

def maladaptive_band(raw):
    if raw <= 5:
        return "Below Average"
    if raw <= 14:
        return "Average"
    return "Elevated"

def age_equiv(code, raw):
    ceiling = _AGE_CEILING_MONTHS.get(code, 216)
    mx = max_raw(code)
    frac = 0 if mx == 0 else raw / mx
    months = int(max(0, min(round(frac * ceiling), ceiling)))
    return "{}:{:02d}".format(months // 12, months % 12)
