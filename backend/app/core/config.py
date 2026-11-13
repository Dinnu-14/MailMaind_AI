"""Application settings, read from environment variables (.env supported)."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths:
# Root directory of the repository
ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]

# Load .env files if present (checked in root, then backend)
if (ROOT_DIR / ".env").exists():
    load_dotenv(ROOT_DIR / ".env")
elif (BACKEND_DIR / ".env").exists():
    load_dotenv(BACKEND_DIR / ".env")
else:
    load_dotenv()


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        # Fallback to local SQLite only when DATABASE_URL is not set (e.g. local dev)
        data_dir = BACKEND_DIR / "data"
        data_dir.mkdir(exist_ok=True)
        return f"sqlite:///{data_dir / 'app.db'}"
    # Convert postgres:// or postgresql:// scheme if needed (e.g. Neon, Supabase, Heroku, Render)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Settings:
    app_name: str = "MailMind AI – Personalized Intelligent Email Classification and Management System"
    app_version: str = "2.0.0"
    
    # Environment
    env: str = os.getenv("ENVIRONMENT", "production").strip().lower()
    secret_key: str = os.getenv("SECRET_KEY", "mailmind-ai-super-secret-key-change-in-production").strip()
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "mailmind-jwt-secret-key-change-in-production").strip()
    
    # Database
    database_url: str = _database_url()
    
    # Google OAuth 2.0 Credentials
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
    
    # LLM / Gemini API Configuration
    llm_api_key: str = (os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    gemini_api_key: str = llm_api_key  # alias for backwards compatibility
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    
    # URLs and CORS
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173").strip()
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000").strip()
    cors_origins: list[str] = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if o.strip()
    ]
    cors_origin_regex: str | None = os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app").strip() or None
    
    # Paths for ML artifacts and datasets
    trained_models_dir: Path = ROOT_DIR / "trained_models"
    dataset_dir: Path = ROOT_DIR / "dataset"
    sample_emails_path: Path = BACKEND_DIR / "data" / "sample_emails.json"

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def gemini_configured(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def google_oauth_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


settings = Settings()
