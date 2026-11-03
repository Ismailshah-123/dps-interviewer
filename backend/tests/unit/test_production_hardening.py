import os
import pytest


def test_production_rejects_groq_without_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 40)
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "false")
    monkeypatch.setenv("EXPOSE_DEMO_RESET_TOKEN", "false")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "a-real-production-password")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("TRANSCRIPTION_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    from pydantic import ValidationError
    from app.core.config import Settings
    with pytest.raises(ValidationError, match="groq_api_key"):
        Settings()


def test_production_accepts_groq_with_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 40)
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "false")
    monkeypatch.setenv("EXPOSE_DEMO_RESET_TOKEN", "false")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "a-real-production-password")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("TRANSCRIPTION_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    from app.core.config import Settings
    s = Settings()
    assert s.transcription_provider == "groq"

