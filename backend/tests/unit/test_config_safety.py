import pytest
from pydantic import ValidationError
from app.core.config import Settings


def base(**overrides):
    values = {
        "secret_key": "x" * 64,
        "environment": "development",
        "database_url": "sqlite+aiosqlite:///./dps.db",
        "auto_create_schema": True,
        "expose_demo_reset_token": True,
        "default_admin_password": "change-me-immediately",
        "cors_origins": ["http://localhost:5173"],
    }
    values.update(overrides)
    return values


def test_production_rejects_auto_schema():
    with pytest.raises(ValidationError):
        Settings(**base(environment="production", auto_create_schema=True, expose_demo_reset_token=False, default_admin_password="StrongPassword123!", database_url="postgresql+asyncpg://u:p@db/app"))


def test_production_requires_postgres():
    with pytest.raises(ValidationError):
        Settings(**base(environment="production", auto_create_schema=False, expose_demo_reset_token=False, default_admin_password="StrongPassword123!"))


def test_production_rejects_demo_reset_token_and_default_password():
    with pytest.raises(ValidationError):
        Settings(**base(environment="production", auto_create_schema=False, expose_demo_reset_token=True, default_admin_password="StrongPassword123!", database_url="postgresql+asyncpg://u:p@db/app"))
    with pytest.raises(ValidationError):
        Settings(**base(environment="production", auto_create_schema=False, expose_demo_reset_token=False, default_admin_password="change-me-immediately", database_url="postgresql+asyncpg://u:p@db/app"))


def test_production_valid_configuration_is_accepted():
    settings = Settings(**base(environment="production", auto_create_schema=False, expose_demo_reset_token=False, default_admin_password="StrongPassword123!", database_url="postgresql+asyncpg://u:p@db/app"))
    assert settings.environment == "production"


def test_deterministic_providers_refused_outside_test_environment():
    import pytest
    from app.core.config import Settings
    with pytest.raises(ValueError):
        Settings(secret_key="x" * 40, environment="development", transcription_provider="deterministic-test")
    assert Settings(secret_key="x" * 40, environment="test", transcription_provider="deterministic-test").transcription_provider == "deterministic-test"


def test_list_settings_accept_comma_separated_env(monkeypatch):
    from app.core.config import Settings
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, https://interviews.example.org")
    monkeypatch.setenv("ALLOWED_AUDIO_MIME_TYPES", "audio/webm,audio/ogg")
    s = Settings(secret_key="x" * 40)
    assert s.cors_origins == ["http://localhost:5173", "https://interviews.example.org"]
    assert s.allowed_audio_mime_types == ["audio/webm", "audio/ogg"]
