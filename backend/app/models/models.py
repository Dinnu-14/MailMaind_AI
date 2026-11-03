from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text, UniqueConstraint)

from app.database import Base


def _now():
    return datetime.utcnow()


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    key = Column(String(40), unique=True, nullable=False)
    name = Column(String(80), nullable=False)
    description = Column(String(300), default="")
    icon = Column(String(40), default="user")
    is_active = Column(Boolean, default=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), unique=True, nullable=False)
    profession = Column(String(120), default="")
    categories = Column(JSON, default=list)
    boosted_categories = Column(JSON, default=list)
    excluded_categories = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    onboarded = Column(Boolean, default=False)
    version = Column(Integer, default=1)  # bumped on every change -> triggers reclassification
    last_engine = Column(String(20), default="")
    last_error = Column(Text, nullable=True)
    classified_at = Column(DateTime, nullable=True)


class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True)
    sender_name = Column(String(120), nullable=False)
    sender_email = Column(String(200), nullable=False)
    subject = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False)
    category = Column(String(60), nullable=False)  # dataset label (not the personalised one)
    is_read = Column(Boolean, default=False)
    summary_json = Column(Text, nullable=True)
    summary_engine = Column(String(20), nullable=True)


class EmailClassification(Base):
    __tablename__ = "email_classifications"
    __table_args__ = (UniqueConstraint("email_id", "profile_id", name="uq_email_profile"),)
    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    is_important = Column(Boolean, default=False)
    category = Column(String(60), nullable=False)
    priority = Column(String(10), nullable=False)  # High | Medium | Low | Other
    relevance_score = Column(Integer, default=0)
    reason = Column(Text, default="")
    engine = Column(String(20), default="rules")  # rules | gemini
    pref_version = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), unique=True, nullable=False)
    state = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_now)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(12), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    engine = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=_now)


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    expected_important = Column(Boolean, nullable=True)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=_now)


class Activity(Base):
    __tablename__ = "activity"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    kind = Column(String(30), nullable=False)
    text = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=_now)
