"""Profile, preference, conversation and seeding helpers."""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (Activity, ChatMessage, Conversation, Email, EmailClassification,
                        UserPreference, UserProfile)
from app.services.lexicon import PROFILE_PRESETS, join_list

PROFILE_META = [
    ("student", "Student", "College updates, exams, placements, internships, jobs and interviews.", "graduation-cap"),
    ("businessperson", "Businessperson", "Proposals, client enquiries, invoices and meetings.", "briefcase"),
    ("job_seeker", "Job Seeker", "Job alerts, recruiters, interviews, assessments and offers.", "search"),
    ("professional", "Working Professional", "Office communication, project updates, HR and clients.", "building-2"),
    ("custom", "Custom", "Start from scratch and describe your needs to the assistant.", "sparkles"),
]
GREETING = "Hi! Welcome to your AI Smart Email Assistant. What is your profession?"


def now():
    return datetime.utcnow()


def log_activity(db: Session, profile_id: int, kind: str, text: str):
    db.add(Activity(profile_id=profile_id, kind=kind, text=text[:300]))


def load_sample_emails(db: Session, reset: bool = False) -> int:
    data = json.loads(settings.sample_emails_path.read_text(encoding="utf-8"))
    existing = {e.id: e for e in db.query(Email)}
    for d in data:
        e = existing.get(d["id"]) or Email(id=d["id"])
        e.sender_name, e.sender_email = d["sender_name"], d["sender_email"]
        e.subject, e.body, e.category = d["subject"], d["body"], d["category"]
        e.date = datetime.fromisoformat(d["date"])
        if reset or d["id"] not in existing:
            e.is_read = d.get("is_read", False)
            e.summary_json = e.summary_engine = None
        db.add(e)
    db.commit()
    return len(data)


def apply_preset(db: Session, profile: UserProfile, pref: UserPreference):
    preset = PROFILE_PRESETS[profile.key]
    pref.profession = preset["profession"]
    pref.categories = list(preset["categories"])
    pref.boosted_categories, pref.excluded_categories, pref.keywords = [], [], []
    pref.onboarded = profile.key != "custom"
    pref.version = (pref.version or 0) + 1


def reset_conversation(db: Session, profile: UserProfile) -> Conversation:
    conv = db.query(Conversation).filter_by(profile_id=profile.id).first()
    if conv:
        db.query(ChatMessage).filter_by(conversation_id=conv.id).delete()
    else:
        conv = Conversation(profile_id=profile.id)
        db.add(conv)
        db.flush()
    if profile.key == "custom":
        conv.state = {"stage": "ask_profession", "pending": None, "profession_key": None}
        text = GREETING
    else:
        preset = PROFILE_PRESETS[profile.key]
        conv.state = {"stage": "ready", "pending": None, "profession_key": profile.key}
        text = (f"You're using the {profile.name} demo profile. I'm prioritizing "
                f"{join_list(preset['categories'])}. Ask me to change anything, for example "
                f"\"include internships\" or \"stop prioritizing shopping emails\".")
    db.add(ChatMessage(conversation_id=conv.id, role="assistant", content=text))
    db.commit()
    return conv


def seed(db: Session):
    if db.query(UserProfile).count() == 0:
        for i, (key, name, desc, icon) in enumerate(PROFILE_META):
            p = UserProfile(key=key, name=name, description=desc, icon=icon, is_active=(key == "custom"))
            db.add(p)
            db.flush()
            pref = UserPreference(profile_id=p.id)
            apply_preset(db, p, pref)
            db.add(pref)
            db.flush()
            reset_conversation(db, p)
        db.commit()
    if db.query(Email).count() == 0:
        load_sample_emails(db)


def active_profile(db: Session) -> UserProfile:
    p = db.query(UserProfile).filter_by(is_active=True).first()
    if not p:
        p = db.query(UserProfile).filter_by(key="custom").first()
        p.is_active = True
        db.commit()
    return p


def get_pref(db: Session, profile: UserProfile) -> UserPreference:
    return db.query(UserPreference).filter_by(profile_id=profile.id).one()


def get_conversation(db: Session, profile: UserProfile) -> Conversation:
    conv = db.query(Conversation).filter_by(profile_id=profile.id).first()
    return conv or reset_conversation(db, profile)


def clear_classifications(db: Session):
    db.query(EmailClassification).delete()
    db.commit()
