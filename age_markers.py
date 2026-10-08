"""
age_markers.py
==============
Age start markers for each subdomain of the Vineland-3 Comprehensive Interview Form.
"""

AGE_MARKERS = {'rec': [{'age_label': '0', 'start_item': 1}, {'age_label': '1', 'start_item': 18}, {'age_label': '2', 'start_item': 27}, {'age_label': '3+', 'start_item': 33}], 'exp': [{'age_label': '0', 'start_item': 1}, {'age_label': '1', 'start_item': 12}, {'age_label': '2', 'start_item': 29}, {'age_label': '3+', 'start_item': 43}], 'wrn': [{'age_label': '0-2', 'start_item': 1}, {'age_label': '3', 'start_item': 6}, {'age_label': '4', 'start_item': 9}, {'age_label': '5', 'start_item': 14}, {'age_label': '6-7', 'start_item': 25}, {'age_label': '8+', 'start_item': 30}], 'per': [{'age_label': '0', 'start_item': 1}, {'age_label': '1', 'start_item': 9}, {'age_label': '2', 'start_item': 25}, {'age_label': '3', 'start_item': 33}, {'age_label': '4+', 'start_item': 45}], 'dom': [{'age_label': '0-2', 'start_item': 1}, {'age_label': '3-4', 'start_item': 5}, {'age_label': '5-6', 'start_item': 10}, {'age_label': '7-8', 'start_item': 18}, {'age_label': '9+', 'start_item': 25}], 'cmm': [{'age_label': '0-2', 'start_item': 2}, {'age_label': '3-4', 'start_item': 10}, {'age_label': '5', 'start_item': 13}, {'age_label': '6-7', 'start_item': 25}, {'age_label': '8-9', 'start_item': 33}, {'age_label': '10-11', 'start_item': 38}, {'age_label': '12+', 'start_item': 44}], 'ipr': [{'age_label': '0', 'start_item': 1}, {'age_label': '1', 'start_item': 14}, {'age_label': '2', 'start_item': 23}, {'age_label': '3', 'start_item': 31}, {'age_label': '4', 'start_item': 36}, {'age_label': '5+', 'start_item': 40}], 'pla': [{'age_label': '0', 'start_item': 1}, {'age_label': '1', 'start_item': 7}, {'age_label': '2', 'start_item': 19}, {'age_label': '3', 'start_item': 22}, {'age_label': '4+', 'start_item': 28}], 'cop': [{'age_label': '0', 'start_item': 1}, {'age_label': '1', 'start_item': 6}, {'age_label': '2', 'start_item': 14}, {'age_label': '3', 'start_item': 17}, {'age_label': '4-5', 'start_item': 22}, {'age_label': '6+', 'start_item': 28}], 'gmo': [{'age_label': '0', 'start_item': 1}, {'age_label': '1', 'start_item': 20}, {'age_label': '2', 'start_item': 33}, {'age_label': '3+', 'start_item': 38}], 'fmo': [{'age_label': '0', 'start_item': 1}, {'age_label': '1', 'start_item': 10}, {'age_label': '2', 'start_item': 14}, {'age_label': '3', 'start_item': 20}, {'age_label': '4', 'start_item': 26}, {'age_label': '5+', 'start_item': 30}]}

def get_recommended_start_item(subdomain, age_years):
    """
    Return the recommended starting-item marker for a subdomain and age.
    Returns the marker dict {'age_label', 'start_item'} whose age range
    includes age_years.
    """
    markers = AGE_MARKERS.get(subdomain, [])
    best_marker = markers[0] if markers else {'age_label': '0', 'start_item': 1}
    for marker in markers:
        label = marker['age_label']
        if '+' in label:
            min_age = int(label.replace('+', '').strip())
            if age_years >= min_age:
                best_marker = marker
        elif '-' in label:
            parts = label.split('-')
            min_age, max_age = int(parts[0].strip()), int(parts[1].strip())
            if min_age <= age_years <= max_age:
                best_marker = marker
                return best_marker
        else:
            if age_years >= int(label.strip()):
                best_marker = marker
    return best_marker
