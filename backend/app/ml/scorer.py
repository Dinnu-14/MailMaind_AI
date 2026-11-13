"""Personalized priority scoring and explainability engine."""
import re
from typing import Any
from app.services.lexicon import (
    CATEGORIES, CATEGORY_SIGNALS, JOB_ROLE_CATEGORIES,
    join_list, keyword_hit
)

URGENCY_REGEX = re.compile(
    r"deadline|urgent|expires|last date|ends tonight|closes on|within 24 hours|immediately|"
    r"\b(before|by|until|due)\b[^.]{0,20}\b(november|nov|friday|tonight|tomorrow)|due on|starts sunday|tomorrow",
    re.I
)


def priority_from_score(score: int) -> str:
    """Map numeric 0-100 score to priority level."""
    if score >= 80:
        return "High"
    if score >= 60:
        return "Medium"
    if score >= 40:
        return "Low"
    return "Other"


def infer_fine_category(subject: str, body: str, default_cat: str) -> str:
    """Infer fine-grained category using keyword signals."""
    sub_low, body_low = subject.lower(), body.lower()
    best_cat, best_score = default_cat, -1.0
    for cat, signals in CATEGORY_SIGNALS.items():
        s = 0.0
        for sig in signals:
            if sig in sub_low:
                s += 3.0
            if sig in body_low:
                s += 1.0
        if cat == default_cat:
            s += 2.5
        if s > best_score:
            best_cat, best_score = cat, s
    return best_cat if best_score > 0 else (default_cat if default_cat in CATEGORIES else "Other")


def calculate_personalized_score(
    email_text: str,
    subject: str,
    body: str,
    dataset_category: str,
    ml_prediction: dict[str, Any],
    user_prefs: dict[str, Any],
    is_read: bool = False
) -> dict[str, Any]:
    """
    Calculate personalized relevance score (0-100), priority level, and reason.
    Combines ML predicted category with user preference filters and urgency indicators.
    """
    fine_category = infer_fine_category(subject, body, dataset_category)
    ml_category = ml_prediction.get("category", "Work")
    ml_confidence = ml_prediction.get("confidence", 0.5)

    wanted = user_prefs.get("categories", [])
    boosted = user_prefs.get("boosted", [])
    excluded = user_prefs.get("excluded", [])
    keywords = user_prefs.get("keywords", [])

    hits = [k for k in keywords if keyword_hit(k, email_text)]
    urgent = bool(URGENCY_REGEX.search(f"{subject} {body}"))
    reasons: list[str] = []

    # If no preferences configured yet
    if not wanted and not keywords:
        return {
            "is_important": False,
            "category": fine_category,
            "priority": "Other",
            "relevance_score": 0,
            "reason": "No preferences yet. Tell the assistant what matters to you and this email will be re-ranked.",
            "ml_category": ml_category,
            "ml_confidence": ml_confidence,
        }

    # Base scoring
    if fine_category in wanted:
        score = 70
        reasons.append(f"{fine_category} is one of the topics you asked to prioritize.")
        if fine_category in boosted:
            score += 10
            reasons.append("You asked to boost this topic.")
        if keywords and fine_category in JOB_ROLE_CATEGORIES:
            if hits:
                score += 14
                reasons.append(f"It matches your focus on {join_list([h.title() for h in hits])}.")
            else:
                score -= 35
                reasons.append(f"It is a {fine_category.lower()} but does not match your focus on {join_list([k.title() for k in keywords])}.")
        elif hits:
            score += 8
            reasons.append(f"It also mentions {join_list([h.title() for h in hits])}.")
        if urgent:
            score += 10
            reasons.append("It contains a deadline or time-sensitive action.")
        if not is_read:
            score += 3
    else:
        score = 10
        if hits:
            score += 35 + 8 * (len(hits) - 1)
            reasons.append(f"Mentions {join_list([h.title() for h in hits])}.")
        if urgent:
            score += 10
            reasons.append("Contains a deadline.")
        if not reasons:
            reasons.append(f"{fine_category} is not in your current priority topics.")

    # Apply exclusions
    if fine_category in excluded:
        score = min(score, 20)
        reasons.append(f"You asked to exclude {fine_category}.")

    # Bound score between 0 and 100
    final_score = max(0, min(100, score))
    priority = priority_from_score(final_score)
    is_important = final_score >= 60

    return {
        "is_important": is_important,
        "category": fine_category,
        "priority": priority,
        "relevance_score": final_score,
        "reason": " ".join(reasons),
        "ml_category": ml_category,
        "ml_confidence": ml_confidence,
    }

