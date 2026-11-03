from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Email
from app.routes.common import class_map, cls_out, current, preview_of, to_item
from app.schemas import EmailDetailOut, EmailListOut, SummaryOut
from app.services import search, state, summarizer
from app.services.lexicon import CATEGORIES

router = APIRouter(prefix="/api", tags=["emails"])

Sort = Literal["date_desc", "date_asc", "score_desc"]


def _list(db: Session, important_only: Optional[bool], q, category, priority, unread, sort) -> EmailListOut:
    profile = current(db)
    cls = class_map(db, profile)
    parsed = search.parse_query(q) if q else None
    items = []
    for e in db.query(Email).all():
        c = cls.get(e.id)
        if important_only is True and not (c and c.is_important):
            continue
        if important_only is False and (c and c.is_important):
            continue
        if category and category not in {c.category if c else None, e.category}:
            continue
        if priority and (not c or c.priority != priority):
            continue
        if unread and e.is_read:
            continue
        if parsed and not search.matches(e, c, parsed):
            continue
        items.append((e, c))
    if sort == "date_asc":
        items.sort(key=lambda t: t[0].date)
    elif sort == "score_desc":
        items.sort(key=lambda t: (-(t[1].relevance_score if t[1] else 0), -t[0].date.timestamp()))
    else:
        items.sort(key=lambda t: t[0].date, reverse=True)
    return EmailListOut(total=len(items), items=[to_item(e, c) for e, c in items],
                        query_description=search.describe(parsed) if parsed else "")


def _validate(category, priority):
    if category and category not in CATEGORIES:
        raise HTTPException(422, f"Unknown category '{category}'")
    if priority and priority not in {"High", "Medium", "Low", "Other"}:
        raise HTTPException(422, f"Unknown priority '{priority}'")


@router.get("/categories")
def categories():
    return CATEGORIES


@router.get("/emails", response_model=EmailListOut)
def all_emails(q: Optional[str] = Query(None, max_length=200), category: Optional[str] = None,
               priority: Optional[str] = None, important: Optional[bool] = None, unread: bool = False,
               sort: Sort = "date_desc", db: Session = Depends(get_db)):
    """Every email, relevant or not. Nothing is ever deleted."""
    _validate(category, priority)
    return _list(db, important, q, category, priority, unread, sort)


@router.get("/emails/priority", response_model=EmailListOut)
def priority_emails(q: Optional[str] = Query(None, max_length=200), category: Optional[str] = None,
                    priority: Optional[str] = None, unread: bool = False, sort: Sort = "score_desc",
                    db: Session = Depends(get_db)):
    _validate(category, priority)
    return _list(db, True, q, category, priority, unread, sort)


@router.post("/emails/reload")
def reload_emails(db: Session = Depends(get_db)):
    """Sync: reload the sample dataset and reset read/unread status and cached summaries."""
    n = state.load_sample_emails(db, reset=True)
    profile = state.active_profile(db)
    state.log_activity(db, profile.id, "sync", f"Reloaded {n} sample emails")
    db.commit()
    return {"loaded": n}


@router.get("/emails/{email_id}", response_model=EmailDetailOut)
def email_detail(email_id: int, mark_read: bool = True, db: Session = Depends(get_db)):
    profile = current(db)
    e = db.get(Email, email_id)
    if not e:
        raise HTTPException(404, "Email not found")
    if mark_read and not e.is_read:
        e.is_read = True
        db.commit()
    c = class_map(db, profile).get(e.id)
    data, engine = summarizer.get_summary(db, e)
    item = to_item(e, c)
    return EmailDetailOut(**item.model_dump(), body=e.body, summary=SummaryOut(**data, engine=engine))
