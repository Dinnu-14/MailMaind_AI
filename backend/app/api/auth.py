"""Google OAuth 2.0 & Gmail Integration Endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.integrations.gmail import (
    exchange_code,
    get_google_user_email,
    get_oauth_authorization_url,
    is_oauth_configured,
    sync_gmail_emails,
)
from app.models import GmailOAuthToken
from app.routes.common import current
from app.schemas.schemas import GmailSyncOut, GoogleAuthStatusOut, GoogleAuthUrlOut

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/auth/google/url", response_model=GoogleAuthUrlOut)
def google_auth_url():
    """Retrieve Google OAuth 2.0 authorization URL."""
    if not is_oauth_configured():
        return GoogleAuthUrlOut(
            url="",
            configured=False
        )
    try:
        url = get_oauth_authorization_url()
        return GoogleAuthUrlOut(url=url, configured=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/google/callback")
def google_auth_callback_get(
    code: str = Query(None),
    error: str = Query(None),
    state: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    OAuth 2.0 callback endpoint from Google.
    Exchanges authorization code for tokens, stores in PostgreSQL, and redirects to frontend Settings.
    """
    frontend_settings_url = f"{settings.frontend_url}/settings"

    if error:
        return RedirectResponse(f"{frontend_settings_url}?oauth_error={error}")

    if not code:
        return RedirectResponse(f"{frontend_settings_url}?oauth_error=missing_code")

    try:
        tokens = exchange_code(code)
        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 3600)
        user_email = get_google_user_email(access_token) or "connected@gmail.com"

        profile = current(db)
        existing = db.query(GmailOAuthToken).filter_by(profile_id=profile.id).first()
        now = datetime.utcnow()
        expiry_dt = datetime.fromtimestamp(now.timestamp() + expires_in)

        if existing:
            existing.email_address = user_email
            existing.access_token = access_token
            if refresh_token:
                existing.refresh_token = refresh_token
            existing.token_expiry = expiry_dt
            existing.is_active = True
            existing.updated_at = now
        else:
            new_token = GmailOAuthToken(
                profile_id=profile.id,
                email_address=user_email,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=expiry_dt,
                scope=tokens.get("scope", ""),
                is_active=True,
            )
            db.add(new_token)

        db.commit()
        return RedirectResponse(f"{frontend_settings_url}?oauth_status=connected&email={user_email}")
    except Exception as e:
        return RedirectResponse(f"{frontend_settings_url}?oauth_error={str(e)}")


@router.post("/auth/google/callback")
def google_auth_callback_post(
    request: Request,
    db: Session = Depends(get_db)
):
    """Direct JSON callback endpoint for SPAs exchanging an authorization code."""
    # Read payload
    try:
        # Accept either JSON with { "code": "..." }
        data = None
    except Exception:
        pass


@router.get("/auth/google/status", response_model=GoogleAuthStatusOut)
def google_auth_status(db: Session = Depends(get_db)):
    """Check if Gmail account is connected for the active profile."""
    profile = current(db)
    token = db.query(GmailOAuthToken).filter_by(profile_id=profile.id, is_active=True).first()
    return GoogleAuthStatusOut(
        connected=bool(token and token.is_active),
        email=token.email_address if token else None,
        last_synced_at=token.last_synced_at if token else None,
        configured=is_oauth_configured()
    )


@router.post("/auth/google/disconnect")
def google_auth_disconnect(db: Session = Depends(get_db)):
    """Disconnect Gmail integration for active profile."""
    profile = current(db)
    token = db.query(GmailOAuthToken).filter_by(profile_id=profile.id).first()
    if token:
        db.delete(token)
        db.commit()
    return {"status": "disconnected"}


@router.post("/gmail/sync", response_model=GmailSyncOut)
def gmail_sync(db: Session = Depends(get_db)):
    """Trigger on-demand serverless sync of recent emails from connected Gmail."""
    profile = current(db)
    result = sync_gmail_emails(db, profile, max_emails=25)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Sync failed"))
    return GmailSyncOut(
        status="success",
        synced=result.get("synced", 0),
        total_checked=result.get("total_checked", 0),
        last_synced_at=result.get("last_synced_at")
    )

