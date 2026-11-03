from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ClassificationOut(BaseModel):
    email_id: int
    is_important: bool
    category: str
    priority: str
    relevance_score: int
    reason: str
    engine: str


class EmailListItem(BaseModel):
    id: int
    sender_name: str
    sender_email: str
    subject: str
    preview: str
    date: datetime
    dataset_category: str
    is_read: bool
    classification: Optional[ClassificationOut] = None


class EmailListOut(BaseModel):
    total: int
    items: list[EmailListItem]
    query_description: str = ""


class SummaryOut(BaseModel):
    purpose: str
    important_information: list[str]
    deadlines: list[str]
    required_action: str
    sender_request: str
    engine: str


class EmailDetailOut(EmailListItem):
    body: str
    summary: SummaryOut


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    engine: Optional[str] = None
    created_at: datetime


class ChatOut(BaseModel):
    reply: str
    engine: str
    preferences_changed: bool
    classification: Optional[dict] = None
    action: Optional[dict] = None
    ai_error: Optional[str] = None


class PreferencesOut(BaseModel):
    profile_key: str
    profile_name: str
    profession: str
    categories: list[str]
    boosted_categories: list[str]
    excluded_categories: list[str]
    keywords: list[str]
    onboarded: bool
    last_engine: str
    last_error: Optional[str] = None
    classified_at: Optional[datetime] = None


class PreferencesIn(BaseModel):
    profession: Optional[str] = Field(default=None, max_length=120)
    categories: Optional[list[str]] = None
    boosted_categories: Optional[list[str]] = None
    excluded_categories: Optional[list[str]] = None
    keywords: Optional[list[str]] = Field(default=None, max_length=20)


class ClassifyIn(BaseModel):
    engine: Literal["auto", "rules", "gemini"] = "auto"


class FeedbackIn(BaseModel):
    email_id: int
    is_correct: bool
    expected_important: Optional[bool] = None
    comment: str = Field(default="", max_length=500)


class ProfileOut(BaseModel):
    key: str
    name: str
    description: str
    icon: str
    is_active: bool


class SwitchIn(BaseModel):
    key: Literal["student", "businessperson", "job_seeker", "professional", "custom"]
    reset_conversation: bool = False
