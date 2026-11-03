"""Start an isolated backend for Playwright: fresh SQLite DB, ENVIRONMENT=test, deterministic AI providers.

Deterministic providers return fixed synthetic text and are refused by configuration outside
ENVIRONMENT=test, so this server can never be mistaken for the demo.
"""
import os
import shutil
import sys
from pathlib import Path

backend = Path(__file__).resolve().parents[1] / "backend"
work = backend / ".e2e"
shutil.rmtree(work, ignore_errors=True)
work.mkdir()
os.chdir(backend)
os.environ.update({
    "DPS_ENV_FILE": "",  # ignore the developer's backend/.env
    "ENVIRONMENT": "test",
    "SECRET_KEY": "e2e-only-secret-key-not-for-any-real-deployment-000",
    "DATABASE_URL": f"sqlite+aiosqlite:///{(work / 'e2e.db').as_posix()}",
    "STORAGE_ROOT": str(work / "storage"),
    "DEFAULT_ADMIN_EMAIL": "admin@dps.example.com",
    "DEFAULT_ADMIN_PASSWORD": "E2E-Admin-Pass-2026!",
    "TRANSCRIPTION_PROVIDER": "deterministic-test",
    "SUMMARIZATION_PROVIDER": "deterministic-test",
    "CORS_ORIGINS": "http://localhost:5174",
})
sys.path.insert(0, str(backend))
import uvicorn  # noqa: E402

uvicorn.run("app.main:app", host="127.0.0.1", port=8001, log_level="warning")
