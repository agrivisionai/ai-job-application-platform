"""Application configuration.

Every tunable lives here and is sourced from environment variables so that no
secret is ever hard-coded or shipped to the frontend. See ``.env.example``.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


def _csv(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", REPO_ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------------- core ----------------
    app_name: str = "AI Job Application Platform"
    environment: Literal["development", "staging", "production", "test"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"
    timezone: str = "America/Detroit"
    log_level: str = "INFO"
    log_json: bool = False

    secret_key: str = "change-me-dev-only"
    encryption_key: str | None = None
    access_token_expire_minutes: int = 60

    # ---------------- database ----------------
    database_url: str = "sqlite+pysqlite:///./data/jobai.db"
    enable_pgvector: bool = True
    embedding_dim: int = 1536

    # ---------------- redis / celery ----------------
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ---------------- storage ----------------
    storage_dir: str = "./data"

    # ---------------- llm ----------------
    llm_provider: Literal["offline", "anthropic", "openai"] = "offline"
    llm_model: str = "claude-opus-5"
    llm_max_tokens: int = 4000
    llm_temperature: float = 0.2
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    embedding_provider: Literal["offline", "openai"] = "offline"
    embedding_model: str = "text-embedding-3-small"

    # ---------------- job sources ----------------
    source_greenhouse_enabled: bool = True
    source_lever_enabled: bool = True
    source_ashby_enabled: bool = True
    source_smartrecruiters_enabled: bool = True
    source_workable_enabled: bool = True
    source_recruitee_enabled: bool = True
    source_remoteok_enabled: bool = True
    source_arbeitnow_enabled: bool = True
    source_himalayas_enabled: bool = True
    source_jobicy_enabled: bool = True

    greenhouse_boards: list[str] = Field(default_factory=list)
    lever_boards: list[str] = Field(default_factory=list)
    ashby_boards: list[str] = Field(default_factory=list)
    smartrecruiters_companies: list[str] = Field(default_factory=list)
    workable_accounts: list[str] = Field(default_factory=list)
    recruitee_companies: list[str] = Field(default_factory=list)

    source_adzuna_enabled: bool = False
    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None
    source_jooble_enabled: bool = False
    jooble_api_key: str | None = None
    source_usajobs_enabled: bool = False
    usajobs_api_key: str | None = None
    usajobs_user_agent: str | None = None
    source_themuse_enabled: bool = False
    themuse_api_key: str | None = None

    # Manual-only platforms. "manual" is the only accepted value: these sites
    # have no public jobs API and their terms prohibit automated access.
    source_linkedin_mode: Literal["manual"] = "manual"
    source_indeed_mode: Literal["manual"] = "manual"
    source_ziprecruiter_mode: Literal["manual"] = "manual"
    source_dice_mode: Literal["manual"] = "manual"
    source_glassdoor_mode: Literal["manual"] = "manual"

    # ---------------- application automation ----------------
    application_mode: Literal["manual", "assisted", "auto"] = "assisted"
    auto_submit_enabled: bool = False
    min_match_score_to_prepare: int = 70
    min_match_score_to_auto_submit: int = 85
    max_applications_per_day: int = 20
    max_applications_per_week: int = 100
    max_posting_age_days: int = 7
    job_search_interval_minutes: int = 60

    # ---------------- networking ----------------
    recruiter_discovery_enabled: bool = True
    max_connection_requests_per_day: int = 10
    max_outreach_messages_per_day: int = 15
    outreach_requires_approval: bool = True
    followup_days: list[int] = Field(default_factory=lambda: [1, 5, 10])

    source_pdl_enabled: bool = False
    pdl_api_key: str | None = None
    source_hunter_enabled: bool = False
    hunter_api_key: str | None = None

    # ---------------- email ----------------
    gmail_enabled: bool = False
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/v1/oauth/google/callback"
    outlook_enabled: bool = False
    ms_client_id: str | None = None
    ms_client_secret: str | None = None
    ms_tenant_id: str = "common"
    ms_redirect_uri: str = "http://localhost:8000/api/v1/oauth/microsoft/callback"

    smtp_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True

    # ---------------- notifications ----------------
    notify_email_enabled: bool = False
    notify_dashboard_enabled: bool = True
    notify_telegram_enabled: bool = False
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    notify_whatsapp_enabled: bool = False
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from: str | None = None
    twilio_whatsapp_to: str | None = None

    # ---------------- safety ----------------
    automation_paused: bool = False
    external_actions_blocked: bool = False
    http_timeout_seconds: int = 20
    http_max_retries: int = 3
    respect_robots_txt: bool = True
    user_agent: str = "JobAI-Personal-Assistant/1.0 (personal job search)"

    # ---------------- validators ----------------
    @field_validator(
        "greenhouse_boards",
        "lever_boards",
        "ashby_boards",
        "smartrecruiters_companies",
        "workable_accounts",
        "recruitee_companies",
        mode="before",
    )
    @classmethod
    def _split_csv(cls, value):  # noqa: ANN001
        return _csv(value)

    @field_validator("followup_days", mode="before")
    @classmethod
    def _split_days(cls, value):  # noqa: ANN001
        if isinstance(value, str):
            return [int(p) for p in _csv(value)]
        return value

    # ---------------- derived helpers ----------------
    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        if not path.is_absolute():
            path = REPO_ROOT / path
        return path

    @property
    def generated_dir(self) -> Path:
        return self.storage_path / "generated"

    @property
    def upload_dir(self) -> Path:
        return self.storage_path / "uploads"

    def ensure_dirs(self) -> None:
        for path in (self.storage_path, self.generated_dir, self.upload_dir):
            path.mkdir(parents=True, exist_ok=True)

    def llm_configured(self) -> bool:
        if self.llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        return True  # offline provider always available


@lru_cache
def get_settings() -> Settings:
    overrides = {}
    if os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("DATABASE_URL"):
        overrides["database_url"] = "sqlite+pysqlite:///:memory:"
        overrides["environment"] = "test"
    return Settings(**overrides)


settings = get_settings()
