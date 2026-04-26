"""
Configurable weights for the matching engine.
"""

WEIGHTS = {
    "skill_match": 0.40,
    "experience_match": 0.30,
    "education_match": 0.10,
    "contextual_fit": 0.20,
    "critical_skill_penalty": 0.10,  # per missing hard skill
}

# Score label thresholds
LABEL_THRESHOLDS = [
    (85, "Top Match"),
    (70, "Strong Match"),
    (55, "Potential Fit"),
    (40, "Weak Match"),
    (0, "Not Recommended"),
]


def get_label(score: float) -> str:
    """Return a human-readable label for a given score."""
    for threshold, label in LABEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "Not Recommended"
