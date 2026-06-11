from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Sales Assistant CRM"
    app_env: str = "development"
    debug: bool = False
    secret_key: str
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173"

    database_url: str
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    groq_api_key: str = ""
    openai_api_key: str = ""
    ai_primary_provider: str = "groq"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    google_calendar_api_key: str = ""
    gmail_api_key: str = ""

    bland_ai_api_key: str = ""
    bland_ai_base_url: str = "https://api.bland.ai/v1"

    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""
    telegram_admin_chat_id: str = ""

    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    scheduler_enabled: bool = True
    daily_report_hour: int = 8
    meeting_reminder_minutes: int = 15

    frontend_url: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
