"""SQLAlchemy models for MailMind AI."""
from datetime import datetime
from sqlalchemy import (
    JSON, Boolean, Column, DateTime, ForeignKey, Integer,
    String, Text, UniqueConstraint
)
from app.database.session import Base


def _now():
    return datetime.utcnow()


class User(Base):
    """Registered application user."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    full_name = Column(String(120), default="")
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)


class UserProfile(Base):
    """User profile persona (e.g. student, businessperson, custom)."""
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    key = Column(String(40), unique=True, nullable=False, index=True)
    name = Column(String(80), nullable=False)
    description = Column(String(300), default="")
    icon = Column(String(40), default="user")
    is_active = Column(Boolean, default=False)


class UserPreference(Base):
    """Personalized classification preferences linked to a profile."""
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    profession = Column(String(120), default="")
    categories = Column(JSON, default=list)
    boosted_categories = Column(JSON, default=list)
    excluded_categories = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    onboarded = Column(Boolean, default=False)
    version = Column(Integer, default=1)  # bumped on change -> triggers reclassification
    last_engine = Column(String(30), default="")
    last_error = Column(Text, nullable=True)
    classified_at = Column(DateTime, nullable=True)


class Email(Base):
    """Stored email record (from sample dataset or Gmail integration)."""
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    source = Column(String(30), default="sample")  # 'sample' | 'gmail'
    external_id = Column(String(255), nullable=True, index=True)  # Gmail message ID
    sender_name = Column(String(120), nullable=False)
    sender_email = Column(String(200), nullable=False, index=True)
    subject = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    category = Column(String(60), nullable=False)  # baseline dataset category
    is_read = Column(Boolean, default=False)
    summary_json = Column(Text, nullable=True)
    summary_engine = Column(String(30), nullable=True)


class EmailClassification(Base):
    """Personalized priority and relevance classification result per email & profile."""
    __tablename__ = "email_classifications"
    __table_args__ = (UniqueConstraint("email_id", "profile_id", name="uq_email_profile"),)
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    is_important = Column(Boolean, default=False, index=True)
    category = Column(String(60), nullable=False)
    priority = Column(String(10), nullable=False)  # High | Medium | Low | Other
    relevance_score = Column(Integer, default=0, index=True)  # 0 to 100
    reason = Column(Text, default="")
    engine = Column(String(30), default="rules")  # 'rules' | 'ml' | 'gemini'
    pref_version = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)


class GmailOAuthToken(Base):
    """Secure OAuth2 token storage for Gmail integration."""
    __tablename__ = "gmail_tokens"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, unique=True)
    email_address = Column(String(200), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    scope = Column(String(300), default="")
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class Conversation(Base):
    """Chatbot conversation session state."""
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    state = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_now)


class ChatMessage(Base):
    """Individual message in a conversation."""
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(12), nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    engine = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=_now)


class Feedback(Base):
    """User feedback to refine or override AI classification."""
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    expected_important = Column(Boolean, nullable=True)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=_now)


class Activity(Base):
    """Activity log stream."""
    __tablename__ = "activity"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String(30), nullable=False)  # 'preferences' | 'sync' | 'gmail' | 'classify'
    text = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=_now)
