import os
from functools import lru_cache
from typing import Annotated
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "DPS AI Interview System"
    environment: str = "development"
    debug: bool = False
    secret_key: str = Field(min_length=32)
    database_url: str = "sqlite+aiosqlite:///./dps.db"
    storage_root: str = "./storage"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    max_upload_bytes: int = 524_288_000
    # NoDecode: read comma-separated values from env/.env instead of requiring JSON.
    allowed_audio_mime_types: Annotated[list[str], NoDecode] = ["audio/webm", "audio/wav", "audio/mpeg", "audio/mp4", "audio/ogg", "audio/x-m4a"]
    transcription_provider: str = "unavailable"
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_language: str | None = None  # e.g. "ur" or "en" to force; None = auto-detect
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    summarization_provider: str = "unavailable"
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_transcription_model: str = "whisper-large-v3"
    groq_summary_model: str = "openai/gpt-oss-120b"
    groq_max_audio_bytes: int = 26_214_400
    groq_transcription_timeout_seconds: int = 300
    groq_summary_timeout_seconds: int = 180
    groq_summary_max_tokens: int = 4096
    form_extraction_provider: str = "groq"
    groq_form_model: str = "qwen/qwen3.8-27b"
    groq_form_timeout_seconds: int = 180
    groq_form_max_tokens: int = 8192
    groq_max_retries: int = 3
    groq_retry_backoff_seconds: int = 5
    default_admin_email: str = "admin@dps.edu.pk"
    default_admin_password: str = "change-me-immediately"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    auto_create_schema: bool = True
    expose_demo_reset_token: bool = True
    processing_max_attempts: int = 3
    processing_batch_size: int = 2
    retention_days: int = 365
    processing_retry_backoff_seconds: int = 15
    processing_stale_seconds: int = 1800
    processing_worker_batch_size: int = 2
    max_page_limit: int = 100
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout_seconds: int = 30
    db_pool_recycle_seconds: int = 1800
    worker_poll_seconds: float = 2.0
    worker_shutdown_seconds: int = 20
    metrics_enabled: bool = True
    pdf_font_path: str | None = None  # TTF with Arabic-script coverage for Urdu in PDFs
    metrics_path: str = "/metrics"
    request_max_body_bytes: int = 550_000_000

    # DPS_ENV_FILE="" disables the .env file (the test suite does this so a developer's secrets never leak in).
    model_config = SettingsConfigDict(env_file=os.environ.get("DPS_ENV_FILE", ".env") or None, env_file_encoding="utf-8", case_sensitive=False, extra="ignore")


    @model_validator(mode="after")
    def validate_production_safety(self):
        # Deterministic providers return canned text. Allowing them outside automated tests would
        # let a demo show a fabricated transcript or summary as if it were real.
        if "deterministic-test" in (self.transcription_provider, self.summarization_provider) and self.environment != "test":
            raise ValueError("deterministic-test AI providers are only allowed when ENVIRONMENT=test")
        if self.environment == "production":
            if self.auto_create_schema:
                raise ValueError("auto_create_schema must be false in production")
            if self.expose_demo_reset_token:
                raise ValueError("expose_demo_reset_token must be false in production")
            if self.default_admin_password == "change-me-immediately":
                raise ValueError("default_admin_password must be changed in production")
            if not self.database_url.startswith(("postgresql+asyncpg://", "postgresql://")):
                raise ValueError("production requires PostgreSQL")
            if any(origin == "*" for origin in self.cors_origins):
                raise ValueError("wildcard CORS is not allowed in production")
            if self.transcription_provider == "groq" or self.summarization_provider == "groq" or self.form_extraction_provider == "groq":
                if not self.groq_api_key:
                    raise ValueError("groq_api_key is required when a Groq provider is enabled in production")
        return self

    @field_validator("allowed_audio_mime_types", "cors_origins", mode="before")
    @classmethod
    def split_csv(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
