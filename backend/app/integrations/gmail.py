"""Google OAuth 2.0 and Gmail REST API Integration.
Designed for serverless environments (stateless, on-demand execution, no long-running threads).
"""
import base64
import email
from datetime import datetime
import logging
from typing import Any
from urllib.parse import urlencode
import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Activity, Email, GmailOAuthToken, UserProfile
from app.services import classifier, state

logger = logging.getLogger("mailmind.gmail")

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GMAIL_MESSAGES_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def is_oauth_configured() -> bool:
    """Check if Google OAuth environment variables are present."""
    return bool(settings.google_client_id and settings.google_client_secret)


def get_oauth_authorization_url(state_param: str = "") -> str:
    """Generate production-ready Google OAuth 2.0 authorization URL."""
    if not is_oauth_configured():
        raise ValueError("Google OAuth credentials (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) are not configured.")

    redirect_uri = settings.google_redirect_uri or f"{settings.backend_url}/api/auth/google/callback"
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state_param or "mailmind_oauth",
    }
    return f"{GOOGLE_AUTH_BASE}?{urlencode(params)}"


def exchange_code(code: str) -> dict[str, Any]:
    """Exchange authorization code for access and refresh tokens."""
    redirect_uri = settings.google_redirect_uri or f"{settings.backend_url}/api/auth/google/callback"
    data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
    if resp.status_code != 200:
        logger.error(f"Failed to exchange OAuth code: {resp.text}")
        raise ValueError(f"Google OAuth token exchange failed: {resp.text}")
    return resp.json()


def refresh_token_if_needed(db: Session, token_record: GmailOAuthToken) -> str:
    """Check token expiration and refresh if necessary."""
    now = datetime.utcnow()
    # If token expiry exists and is within 2 minutes of expiring, refresh
    if token_record.token_expiry and (token_record.token_expiry - now).total_seconds() < 120:
        if not token_record.refresh_token:
            raise ValueError("No refresh token available. Re-authentication required.")
        data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": token_record.refresh_token,
            "grant_type": "refresh_token",
        }
        resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
        if resp.status_code == 200:
            token_data = resp.json()
            token_record.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            token_record.token_expiry = datetime.fromtimestamp(now.timestamp() + expires_in)
            token_record.updated_at = now
            db.commit()
        else:
            logger.error(f"Token refresh failed: {resp.text}")
            raise ValueError("Failed to refresh Gmail access token.")

    return token_record.access_token


def get_google_user_email(access_token: str) -> str:
    """Retrieve connected user's Google email."""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(GOOGLE_USERINFO_URL, headers=headers, timeout=10)
    if resp.status_code == 200:
        return resp.json().get("email", "")
    return ""


def sync_gmail_emails(db: Session, profile: UserProfile, max_emails: int = 25) -> dict[str, Any]:
    """
    On-demand serverless Gmail sync. Fetches recent messages, stores new ones,
    and classifies them according to user profile preferences.
    """
    token = db.query(GmailOAuthToken).filter_by(profile_id=profile.id, is_active=True).first()
    if not token:
        return {"status": "error", "message": "Gmail is not connected for this profile."}

    access_token = refresh_token_if_needed(db, token)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch recent message IDs
    params = {"maxResults": min(max_emails, 50), "q": "category:primary OR category:updates"}
    list_resp = requests.get(GMAIL_MESSAGES_URL, headers=headers, params=params, timeout=15)
    if list_resp.status_code != 200:
        return {"status": "error", "message": f"Gmail API list messages error: {list_resp.text}"}

    messages_data = list_resp.json().get("messages", [])
    new_emails_count = 0

    for item in messages_data:
        msg_id = item["id"]
        # Check if already saved
        existing = db.query(Email).filter_by(external_id=msg_id).first()
        if existing:
            continue

        # Fetch message detail
        msg_resp = requests.get(f"{GMAIL_MESSAGES_URL}/{msg_id}?format=full", headers=headers, timeout=15)
        if msg_resp.status_code != 200:
            continue
        msg_json = msg_resp.json()

        # Parse headers
        headers_list = msg_json.get("payload", {}).get("headers", [])
        hdr_dict = {h["name"].lower(): h["value"] for h in headers_list}

        subject = hdr_dict.get("subject", "(No Subject)")
        from_hdr = hdr_dict.get("from", "Unknown")
        date_hdr = hdr_dict.get("date", "")

        # Parse sender name and email
        sender_name, sender_email = from_hdr, from_hdr
        if "<" in from_hdr and ">" in from_hdr:
            sender_name = from_hdr.split("<")[0].strip().strip('"')
            sender_email = from_hdr.split("<")[1].split(">")[0].strip()

        # Parse date
        try:
            parsed_date = email.utils.parsedate_to_datetime(date_hdr)
            # Remove tzinfo for naive utc datetime in db
            dt = parsed_date.replace(tzinfo=None) if parsed_date else datetime.utcnow()
        except Exception:
            dt = datetime.utcnow()

        # Extract body text
        snippet = msg_json.get("snippet", "")
        body = snippet or subject

        # Create Email record
        new_email = Email(
            source="gmail",
            external_id=msg_id,
            sender_name=sender_name or "Unknown",
            sender_email=sender_email or "unknown@gmail.com",
            subject=subject,
            body=body,
            date=dt,
            category="Work",  # baseline fallback
            is_read="UNREAD" not in msg_json.get("labelIds", []),
        )
        db.add(new_email)
        new_emails_count += 1

    token.last_synced_at = datetime.utcnow()
    db.commit()

    if new_emails_count > 0:
        # Run classification on new emails
        classifier.classify_all(db, profile, "auto")
        state.log_activity(db, profile.id, "gmail", f"Synced {new_emails_count} new emails from Gmail")
        db.commit()

    return {
        "status": "success",
        "synced": new_emails_count,
        "total_checked": len(messages_data),
        "last_synced_at": token.last_synced_at.isoformat(),
    }

