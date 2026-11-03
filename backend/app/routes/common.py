import re

from sqlalchemy.orm import Session

from app.models import Email, EmailClassification, UserProfile
from app.schemas import ClassificationOut, EmailListItem
from app.services import classifier, state


def preview_of(body: str, n: int = 140) -> str:
    text = re.sub(r"\s+", " ", body).strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "\u2026"


def cls_out(c: EmailClassification | None) -> ClassificationOut | None:
    if not c:
        return None
    return ClassificationOut(email_id=c.email_id, is_important=c.is_important, category=c.category,
                             priority=c.priority, relevance_score=c.relevance_score, reason=c.reason,
                             engine=c.engine)


def to_item(e: Email, c: EmailClassification | None) -> EmailListItem:
    return EmailListItem(id=e.id, sender_name=e.sender_name, sender_email=e.sender_email, subject=e.subject,
                         preview=preview_of(e.body), date=e.date, dataset_category=e.category,
                         is_read=e.is_read, classification=cls_out(c))


def current(db: Session) -> UserProfile:
    """Active profile, with classifications guaranteed to be fresh for its preferences."""
    profile = state.active_profile(db)
    classifier.ensure_classified(db, profile)
    return profile


def class_map(db: Session, profile: UserProfile) -> dict[int, EmailClassification]:
    return {c.email_id: c for c in db.query(EmailClassification).filter_by(profile_id=profile.id)}
