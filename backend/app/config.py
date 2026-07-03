import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

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

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
