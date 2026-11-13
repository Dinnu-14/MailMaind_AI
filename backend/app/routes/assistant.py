"""Assistant API router: health, chat, preferences, classification, profiles, dashboard."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.integrations.gmail import is_oauth_configured
from app.models import (
    Activity, ChatMessage, Email, EmailClassification, Feedback,
    UserPreference, UserProfile
)
from app.routes.common import class_map, current
from app.schemas import (
    ChatIn, ChatMessageOut, ChatOut, ClassifyIn, FeedbackIn,
    HealthOut, PreferencesIn, PreferencesOut, ProfileOut, SwitchIn
)
from app.services import chatbot, classifier, gemini, state
from app.services.lexicon import CATEGORIES

router = APIRouter(prefix="/api", tags=["assistant"])


def _prefs_out(profile: UserProfile, p: UserPreference) -> PreferencesOut:
    return PreferencesOut(
        profile_key=profile.key,
        profile_name=profile.name,
        profession=p.profession or "",
        categories=list(p.categories or []),
        boosted_categories=list(p.boosted_categories or []),
        excluded_categories=list(p.excluded_categories or []),
        keywords=list(p.keywords or []),
        onboarded=bool(p.onboarded),
        last_engine=p.last_engine or "",
        last_error=p.last_error,
        classified_at=p.classified_at
    )


@router.get("/health", response_model=HealthOut)
def health():
    """Application and infrastructure health check."""
    is_postgres = "postgresql" in settings.database_url.lower()
    return HealthOut(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.env,
        gemini_configured=gemini.is_configured(),
        google_oauth_configured=is_oauth_configured(),
        mode="gemini" if gemini.is_configured() else "scikit-learn + rule-based NLP",
        database_type="Hosted PostgreSQL" if is_postgres else "SQLite",
        model_status="MultinomialNB & TF-IDF Loaded"
    )


# ------------------------------------------------------------------ chat
@router.post("/chat", response_model=ChatOut)
def chat(body: ChatIn, db: Session = Depends(get_db)):
    text = body.message.strip()
    if not text:
        raise HTTPException(422, "Message cannot be empty")
    profile = state.active_profile(db)
    return chatbot.handle_message(db, profile, text)


@router.get("/chat/history", response_model=list[ChatMessageOut])
def chat_history(db: Session = Depends(get_db)):
    profile = state.active_profile(db)
    conv = state.get_conversation(db, profile)
    msgs = db.query(ChatMessage).filter_by(conversation_id=conv.id).order_by(ChatMessage.id).all()
    return [
        ChatMessageOut(id=m.id, role=m.role, content=m.content, engine=m.engine, created_at=m.created_at)
        for m in msgs
    ]


@router.post("/chat/reset", response_model=list[ChatMessageOut])
def chat_reset(db: Session = Depends(get_db)):
    profile = state.active_profile(db)
    pref = state.get_pref(db, profile)
    state.apply_preset(db, profile, pref)
    db.commit()
    state.reset_conversation(db, profile)
    state.log_activity(db, profile.id, "preferences", "Conversation and preferences reset")
    db.commit()
    return chat_history(db)


# ------------------------------------------------------------------ preferences
@router.get("/preferences", response_model=PreferencesOut)
def get_preferences(db: Session = Depends(get_db)):
    profile = state.active_profile(db)
    return _prefs_out(profile, state.get_pref(db, profile))


@router.put("/preferences", response_model=PreferencesOut)
def put_preferences(body: PreferencesIn, db: Session = Depends(get_db)):
    profile = state.active_profile(db)
    pref = state.get_pref(db, profile)
    for field in ("categories", "boosted_categories", "excluded_categories"):
        vals = getattr(body, field)
        bad = [v for v in (vals or []) if v not in CATEGORIES]
        if bad:
            raise HTTPException(422, f"Unknown categories: {bad}")
    if body.profession is not None:
        pref.profession = body.profession.strip()
    if body.categories is not None:
        pref.categories = list(dict.fromkeys(body.categories))
    if body.boosted_categories is not None:
        pref.boosted_categories = [c for c in dict.fromkeys(body.boosted_categories) if c in (pref.categories or [])]
    if body.excluded_categories is not None:
        pref.excluded_categories = list(dict.fromkeys(body.excluded_categories))
    if body.keywords is not None:
        pref.keywords = list(dict.fromkeys(k.strip().lower() for k in body.keywords if k.strip()))
    pref.onboarded = True
    pref.version = (pref.version or 0) + 1
    state.log_activity(db, profile.id, "preferences", "Preferences edited in Settings")
    db.commit()
    classifier.classify_all(db, profile, "auto")
    db.refresh(pref)
    return _prefs_out(profile, pref)


# ------------------------------------------------------------------ classification
@router.post("/classify")
def classify(body: ClassifyIn | None = None, db: Session = Depends(get_db)):
    profile = state.active_profile(db)
    engine = body.engine if body else "auto"
    try:
        summary = classifier.classify_all(db, profile, engine)
    except gemini.GeminiError as exc:
        raise HTTPException(502, f"Gemini classification failed: {exc}")
    state.log_activity(db, profile.id, "classify", f"Reclassified {summary['total']} emails using {summary['engine']}")
    db.commit()
    rows = class_map(db, profile)
    return {
        **summary,
        "results": [
            {
                "email_id": c.email_id,
                "is_important": c.is_important,
                "category": c.category,
                "priority": c.priority,
                "relevance_score": c.relevance_score,
                "reason": c.reason,
                "engine": c.engine
            }
            for c in sorted(rows.values(), key=lambda c: c.email_id)
        ]
    }


# ------------------------------------------------------------------ dashboard
@router.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    profile = current(db)
    pref = state.get_pref(db, profile)
    cls = class_map(db, profile)
    emails = db.query(Email).all()
    important = [e for e in emails if cls.get(e.id) and cls[e.id].is_important]
    by_priority = {p: 0 for p in ("High", "Medium", "Low", "Other")}
    by_category: dict[str, int] = {}
    for e in emails:
        c = cls.get(e.id)
        if c:
            by_priority[c.priority] = by_priority.get(c.priority, 0) + 1
            by_category[c.category] = by_category.get(c.category, 0) + 1
    activity = (
        db.query(Activity)
        .filter_by(profile_id=profile.id)
        .order_by(Activity.id.desc())
        .limit(8)
        .all()
    )
    return {
        "profile": {"key": profile.key, "name": profile.name},
        "total": len(emails),
        "important": len(important),
        "other": len(emails) - len(important),
        "unread": sum(1 for e in emails if not e.is_read),
        "unread_important": sum(1 for e in important if not e.is_read),
        "by_priority": by_priority,
        "by_category": dict(sorted(by_category.items(), key=lambda kv: -kv[1])),
        "engine": pref.last_engine or "scikit-learn",
        "engine_error": pref.last_error,
        "gemini_configured": gemini.is_configured(),
        "google_oauth_configured": is_oauth_configured(),
        "onboarded": bool(pref.onboarded),
        "recent_activity": [{"kind": a.kind, "text": a.text, "created_at": a.created_at} for a in activity],
    }


# ------------------------------------------------------------------ feedback
@router.post("/feedback")
def feedback(body: FeedbackIn, db: Session = Depends(get_db)):
    profile = state.active_profile(db)
    if not db.get(Email, body.email_id):
        raise HTTPException(404, "Email not found")
    if not body.is_correct and body.expected_important is None:
        raise HTTPException(422, "expected_important is required when is_correct is false")
    cls = class_map(db, profile).get(body.email_id)
    expected = body.expected_important
    if body.is_correct and expected is None and cls:
        expected = cls.is_important
    db.add(Feedback(
        email_id=body.email_id,
        profile_id=profile.id,
        is_correct=body.is_correct,
        expected_important=expected,
        comment=body.comment
    ))
    state.log_activity(
        db, profile.id, "feedback",
        f"Feedback on email #{body.email_id}: {'correct' if body.is_correct else 'incorrect'}"
    )
    db.commit()
    classifier.classify_all(db, profile, "auto")
    return {"saved": True}


# ------------------------------------------------------------------ profiles
@router.get("/profiles", response_model=list[ProfileOut])
def profiles(db: Session = Depends(get_db)):
    state.active_profile(db)
    order = {k: i for i, (k, *_r) in enumerate(state.PROFILE_META)}
    rows = sorted(db.query(UserProfile).all(), key=lambda p: order.get(p.key, 99))
    return [
        ProfileOut(key=p.key, name=p.name, description=p.description, icon=p.icon, is_active=p.is_active)
        for p in rows
    ]


@router.post("/profiles/switch", response_model=ProfileOut)
def switch_profile(body: SwitchIn, db: Session = Depends(get_db)):
    target = db.query(UserProfile).filter_by(key=body.key).first()
    if not target:
        raise HTTPException(404, "Profile not found")
    for p in db.query(UserProfile).all():
        p.is_active = p.id == target.id
    if body.reset_conversation:
        pref = state.get_pref(db, target)
        state.apply_preset(db, target, pref)
        db.commit()
        state.reset_conversation(db, target)
    state.log_activity(db, target.id, "profile", f"Switched to {target.name} profile")
    db.commit()
    classifier.ensure_classified(db, target)
    return ProfileOut(
        key=target.key, name=target.name, description=target.description,
        icon=target.icon, is_active=True
    )
