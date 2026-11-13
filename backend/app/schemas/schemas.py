"""Pydantic schemas for request validation and response serialization."""
from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ------------------------------------------------------------------ Classification & Emails
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


# ------------------------------------------------------------------ Chat
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


# ------------------------------------------------------------------ Preferences & Profiles
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
    engine: Literal["auto", "rules", "gemini", "ml"] = "auto"


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


# ------------------------------------------------------------------ Machine Learning
class MLPredictIn(BaseModel):
    text: str = Field(..., min_length=1, description="Raw email body or subject line")
    subject: Optional[str] = Field(default="", description="Optional subject line")


class MLPredictOut(BaseModel):
    category: str
    confidence: float
    probabilities: dict[str, float]
    engine: str


class MLMetricsOut(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: str
    vectorizer_name: str
    vocabulary_size: Optional[int] = None
    split_ratio: Optional[str] = None
    test_accuracy: float
    classes: list[str]
    confusion_matrix: Optional[list[list[int]]] = None
    classification_report: Optional[dict[str, Any]] = None


# ------------------------------------------------------------------ Google OAuth & Gmail
class GoogleAuthUrlOut(BaseModel):
    url: str
    configured: bool


class GoogleAuthStatusOut(BaseModel):
    connected: bool
    email: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    configured: bool


class GmailSyncOut(BaseModel):
    status: str
    synced: int
    total_checked: int
    last_synced_at: Optional[str] = None
    message: Optional[str] = None


# ------------------------------------------------------------------ Health Check
class HealthOut(BaseModel):
    model_config = {"protected_namespaces": ()}
    status: str
    app_name: str
    version: str
    environment: str
    gemini_configured: bool
    google_oauth_configured: bool
    mode: str
    database_type: str
    model_status: str

