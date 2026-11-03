"""Personalised email classification: Gemini when available, rule-based fallback otherwise."""
import re
import threading
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Email, EmailClassification, Feedback, UserPreference, UserProfile
from app.services import gemini
from app.services.lexicon import (CATEGORIES, CATEGORY_SIGNALS, JOB_ROLE_CATEGORIES,
                                  join_list, keyword_hit)

URGENCY = re.compile(
    r"deadline|urgent|expires|last date|ends tonight|closes on|within 24 hours|immediately|"
    r"\b(before|by|until|due)\b[^.]{0,20}\b(november|nov|friday|tonight|tomorrow)|due on|starts sunday|tomorrow",
    re.I)


def priority_for(score: int) -> str:
    if score >= 80:
        return "High"
    if score >= 60:
        return "Medium"
    if score >= 40:
        return "Low"
    return "Other"


def email_text(e: Email) -> str:
    return f"{e.sender_name} {e.sender_email} {e.subject} {e.body}"


def infer_category(e: Email) -> str:
    """Infer category from content; the dataset label only breaks ties."""
    subject, body = e.subject.lower(), e.body.lower()
    best, best_score = e.category, -1.0
    for cat, signals in CATEGORY_SIGNALS.items():
        s = 0.0
        for sig in signals:
            if sig in subject:
                s += 3
            if sig in body:
                s += 1
        if cat == e.category:
            s += 2.5
        if s > best_score:
            best, best_score = cat, s
    return best


def prefs_dict(p: UserPreference) -> dict:
    return {
        "profession": p.profession or "",
        "categories": list(p.categories or []),
        "boosted": list(p.boosted_categories or []),
        "excluded": list(p.excluded_categories or []),
        "keywords": list(p.keywords or []),
    }


# ---------------------------------------------------------------- rule-based engine
def rule_classify(e: Email, prefs: dict) -> dict:
    cat = infer_category(e)
    text = email_text(e)
    wanted, boosted, excluded, kws = prefs["categories"], prefs["boosted"], prefs["excluded"], prefs["keywords"]
    hits = [k for k in kws if keyword_hit(k, text)]
    urgent = bool(URGENCY.search(f"{e.subject} {e.body}"))
    parts: list[str] = []

    if not wanted and not kws:
        return dict(email_id=e.id, is_important=False, category=cat, priority="Other", relevance_score=0,
                    reason="No preferences yet. Tell the assistant what matters to you and this email will be re-ranked.",
                    engine="rules")

    if cat in wanted:
        score = 70
        parts.append(f"{cat} is one of the topics you asked to prioritize.")
        if cat in boosted:
            score += 10
            parts.append("You asked to boost this topic.")
        if kws and cat in JOB_ROLE_CATEGORIES:
            if hits:
                score += 14
                parts.append(f"It matches your focus on {join_list([h.title() for h in hits])}.")
            else:
                score -= 35
                parts.append(f"It is a {cat.lower()} but does not match your focus on {join_list([k.title() for k in kws])}.")
        elif hits:
            score += 8
            parts.append(f"It also mentions {join_list([h.title() for h in hits])}.")
        if urgent:
            score += 10
            parts.append("It contains a deadline or time-sensitive action.")
        if not e.is_read:
            score += 3
    else:
        score = 10
        if hits:
            score += 35 + 8 * (len(hits) - 1)
            parts.append(f"It is a {cat.lower()} email, but it mentions {join_list([h.title() for h in hits])}, which you follow.")
        else:
            shown = join_list(wanted[:4]) if wanted else "your keywords"
            parts.append(f"{cat} is not among the topics you prioritize ({shown}).")

    if cat in excluded:
        score = min(score, 15)
        parts.append("You asked to stop prioritizing this topic.")

    score = max(0, min(100, score))
    important = score >= 40
    return dict(email_id=e.id, is_important=important, category=cat,
                priority=priority_for(score) if important else "Other",
                relevance_score=score, reason=" ".join(parts), engine="rules")


# ---------------------------------------------------------------- gemini engine
GEMINI_SYSTEM = (
    "You are an email triage engine. Judge each email's relevance to ONE specific user, based on the "
    "meaning of the email (sender, subject and body), not just keywords. Respond with JSON only."
)


def _gemini_prompt(batch: list[Email], prefs: dict) -> str:
    emails = [{"email_id": e.id, "from": f"{e.sender_name} <{e.sender_email}>", "subject": e.subject,
               "body": e.body[:700]} for e in batch]
    return (
        f"USER PROFILE\nProfession: {prefs['profession'] or 'unknown'}\n"
        f"Topics the user wants prioritized: {prefs['categories']}\n"
        f"Topics the user wants boosted: {prefs['boosted']}\n"
        f"Topics the user does NOT want: {prefs['excluded']}\n"
        f"Focus keywords (roles/skills): {prefs['keywords']}\n\n"
        f"ALLOWED CATEGORIES: {CATEGORIES}\n\n"
        "For every email return an object with: email_id (int), is_important (bool), category (one of the "
        "allowed categories, chosen from the email content), priority (High|Medium|Low|Other), "
        "relevance_score (0-100), reason (one sentence explaining why, referring to the user's needs). "
        "Rules: High = 80-100, Medium = 60-79, Low = 40-59, Other = below 40 and is_important=false. "
        "Return a JSON array with exactly one object per email.\n\n"
        f"EMAILS\n{emails}"
    )


def _validate_gemini_row(row: dict, valid_ids: set[int]) -> dict | None:
    try:
        eid = int(row["email_id"])
        score = max(0, min(100, int(round(float(row["relevance_score"])))))
        cat = row.get("category")
        if eid not in valid_ids or cat not in CATEGORIES:
            return None
        important = bool(row.get("is_important")) and score >= 40
        return dict(email_id=eid, is_important=important, category=cat,
                    priority=priority_for(score) if important else "Other",
                    relevance_score=score, reason=str(row.get("reason", ""))[:400], engine="gemini")
    except (KeyError, TypeError, ValueError):
        return None


def gemini_classify(emails: list[Email], prefs: dict, batch_size: int = 15) -> dict[int, dict]:
    results: dict[int, dict] = {}
    for i in range(0, len(emails), batch_size):
        batch = emails[i:i + batch_size]
        data = gemini.generate_json(_gemini_prompt(batch, prefs), system=GEMINI_SYSTEM)
        if isinstance(data, dict):
            data = data.get("emails") or data.get("results") or []
        valid = {e.id for e in batch}
        for row in data if isinstance(data, list) else []:
            clean = _validate_gemini_row(row, valid) if isinstance(row, dict) else None
            if clean:
                results[clean["email_id"]] = clean
    return results


# ---------------------------------------------------------------- orchestration
def _apply_feedback(db: Session, profile_id: int, row: dict) -> dict:
    fb = (db.query(Feedback)
          .filter(Feedback.email_id == row["email_id"], Feedback.profile_id == profile_id,
                  Feedback.expected_important.isnot(None))
          .order_by(Feedback.id.desc()).first())
    if not fb:
        return row
    if fb.expected_important and not row["is_important"]:
        row.update(is_important=True, relevance_score=max(row["relevance_score"], 65), priority="Medium",
                   reason="You marked this email as important. " + row["reason"])
    elif not fb.expected_important and row["is_important"]:
        row.update(is_important=False, relevance_score=min(row["relevance_score"], 20), priority="Other",
                   reason="You marked this email as not important. " + row["reason"])
    return row


_lock = threading.RLock()  # concurrent requests must not classify the same profile at the same time


def classify_all(db: Session, profile: UserProfile, engine: str = "auto") -> dict:
    with _lock:
        try:
            return _classify_all(db, profile, engine)
        except IntegrityError:  # another worker process inserted the same rows first
            db.rollback()
            return _classify_all(db, profile, engine)


def _classify_all(db: Session, profile: UserProfile, engine: str = "auto") -> dict:
    """(Re)classify every email for the profile and persist the results.

    engine: "auto" (Gemini if available, else rules), "rules", or "gemini" (raises if unavailable).
    Returns a summary that states honestly which engine produced the results.
    """
    pref = db.query(UserPreference).filter_by(profile_id=profile.id).one()
    prefs = prefs_dict(pref)
    emails = db.query(Email).order_by(Email.id).all()
    rows: dict[int, dict] = {}
    used, error = "rules", None

    if engine == "gemini" and not gemini.is_configured():
        raise gemini.GeminiError("GEMINI_API_KEY is not configured on the server")
    want_gemini = engine == "gemini" or (engine == "auto" and gemini.is_available())
    if engine == "auto" and gemini.is_configured() and not gemini.is_available():
        error = f"Gemini temporarily skipped after a recent failure: {gemini.last_error}"

    if want_gemini and (prefs["categories"] or prefs["keywords"]):
        try:
            rows = gemini_classify(emails, prefs)
            used = "gemini"
        except gemini.GeminiError as exc:
            if engine == "gemini":
                raise
            error = f"Gemini failed ({exc}); used the local rule-based classifier instead."
            rows = {}

    fallback_count = 0
    for e in emails:
        if e.id not in rows:
            rows[e.id] = rule_classify(e, prefs)
            fallback_count += 1
    if used == "gemini" and fallback_count == len(emails):
        used = "rules"
    elif used == "gemini" and fallback_count:
        error = f"Gemini returned no valid result for {fallback_count} email(s); rules filled the gap."

    existing = {c.email_id: c for c in db.query(EmailClassification).filter_by(profile_id=profile.id)}
    now = datetime.utcnow()
    for e in emails:
        row = _apply_feedback(db, profile.id, rows[e.id])
        c = existing.get(e.id) or EmailClassification(email_id=e.id, profile_id=profile.id)
        c.is_important, c.category, c.priority = row["is_important"], row["category"], row["priority"]
        c.relevance_score, c.reason, c.engine = row["relevance_score"], row["reason"], row["engine"]
        c.pref_version, c.created_at = pref.version, now
        db.add(c)
    pref.last_engine, pref.last_error, pref.classified_at = used, error, now
    db.commit()
    important = sum(1 for r in rows.values() if r["is_important"])
    return {"engine": used, "error": error, "total": len(emails), "important": important,
            "other": len(emails) - important, "gemini_configured": gemini.is_configured()}


def ensure_classified(db: Session, profile: UserProfile) -> None:
    """Reclassify only when preferences changed or emails are unclassified."""
    def stale() -> bool:
        pref = db.query(UserPreference).filter_by(profile_id=profile.id).one()
        total = db.query(Email).count()
        fresh = (db.query(EmailClassification)
                 .filter_by(profile_id=profile.id, pref_version=pref.version).count())
        return fresh < total

    if not stale():
        return
    with _lock:
        db.expire_all()
        if stale():  # re-check: another request may have finished while we waited
            classify_all(db, profile, "auto")
