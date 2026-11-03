"""Application settings, read from environment variables (.env supported)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]  # backend/
load_dotenv(BASE_DIR / ".env")


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        (BASE_DIR / "data").mkdir(exist_ok=True)
        return f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"
    # Render/Heroku style URLs
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Settings:
    app_name = "AI Smart Email Assistant"
    database_url = _database_url()
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    cors_origins = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if o.strip()
    ]
    # Optional regex, e.g. https://.*\.vercel\.app to allow Vercel preview URLs
    cors_origin_regex = os.getenv("CORS_ORIGIN_REGEX", "").strip() or None
    sample_emails_path = BASE_DIR / "data" / "sample_emails.json"

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)


settings = Settings()
