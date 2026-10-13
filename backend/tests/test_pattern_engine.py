import pytest
from pattern_engine import analyze_asd_patterns


def test_classic_asd_pattern():
    # Classic ASD with co-deficit -> high >= 2
    # soc_ss < com_ss < dls_ss and mot_ss >= 85 and abs(com_ss - soc_ss) < 12
    scores = {
        "soc_ss": 62,
        "com_ss": 72,
        "dls_ss": 82,
        "mot_ss": 92,
        "abc": 71,
    }
    analysis = analyze_asd_patterns(scores)
    pattern_names = [p["name"] for p in analysis["patterns"]]
    assert "Classic ASD Adaptive Profile" in pattern_names
    assert "Social-Communication Co-Deficit" in pattern_names
    assert "Motor Preservation with Social-Communication Deficit" in pattern_names
    assert analysis["asd_profile_likelihood"]["label"] == "Strongly Consistent with ASD-Related Adaptive Profile"


def test_high_functioning_pattern():
    # soc_ss < com_ss and abs(com_ss - dls_ss) <= 10 and 70 <= abc <= 95
    scores = {
        "soc_ss": 68,
        "com_ss": 80,
        "dls_ss": 82,
        "mot_ss": 90,
        "abc": 77,
    }
    analysis = analyze_asd_patterns(scores)
    pattern_names = [p["name"] for p in analysis["patterns"]]
    assert "High-Functioning ASD Adaptive Profile" in pattern_names


def test_severe_asd_pattern():
    # abc < 70 and soc_ss < 70 and com_ss < 70
    scores = {
        "soc_ss": 52,
        "com_ss": 55,
        "dls_ss": 60,
        "mot_ss": 70,
        "abc": 56,
    }
    analysis = analyze_asd_patterns(scores)
    pattern_names = [p["name"] for p in analysis["patterns"]]
    assert "Severe ASD Adaptive Profile" in pattern_names
    assert "Global Adaptive Behavior Deficit" in pattern_names
