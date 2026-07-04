import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator

# Reuse the same SQLite file the original Flask app used, at the repo root
# (backend/app/config.py -> parents[2] is the repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "expense_tracker.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(REPO_ROOT / ".env"), extra="ignore")

    secret_key: str = "dev-secret-key-change-in-production"
    groq_api_key: str | None = None
    bill_ocr_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    database_path: Path = DEFAULT_DB_PATH
    cors_origins: str = "http://localhost:5173"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    # Only set this true when the app is actually served over HTTPS - browsers
    # silently drop Secure cookies on plain HTTP (including local dev and tests).
    cookie_secure: bool = False
    # "strict" for same-origin deployments (frontend and backend behind the same
    # domain, e.g. via the Vite dev proxy). Cross-origin deployments (e.g.
    # frontend on Vercel, backend on Railway) must use "none" so the browser
    # attaches the cookie to cross-site API calls - which requires cookie_secure
    # to also be true, since browsers drop SameSite=None cookies without Secure.
    cookie_samesite: str = "strict"

    # SMTP settings for sending password-reset emails (Forgot Password feature).
    # If smtp_host is left unset, forgot-password requests still return the
    # generic success message, but no email is actually sent.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True
    # Base URL of the deployed frontend, used to build the password-reset link
    # emailed to users.
    frontend_base_url: str = "http://localhost:5173"
    # How long a password-reset link stays valid, in minutes.
    password_reset_token_expire_minutes: int = 30

    # Google and LinkedIn OAuth login (optional - a provider's login button
    # redirects to a clear error instead of crashing if its id/secret is unset).
    google_client_id: str | None = None
    google_client_secret: str | None = None
    linkedin_client_id: str | None = None
    linkedin_client_secret: str | None = None
    microsoft_client_id: str | None = None
    microsoft_client_secret: str | None = None
    # Base URL the backend itself is reachable at - used to build the fixed
    # redirect_uri sent to each OAuth provider (must exactly match what's
    # registered in that provider's console).
    backend_base_url: str = "http://localhost:5001"

    @field_validator("frontend_base_url", "backend_base_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _validate_cookie_flags(self) -> "Settings":
        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise ValueError("cookie_secure must be true when cookie_samesite is 'none'")
        return self


settings = Settings()
