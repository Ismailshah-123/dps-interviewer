# Deployment Guide

## Local demo
1. Create a Python 3.11-3.13 environment.
2. Install backend dependencies with `pip install -e '.[dev]'`.
3. Copy `.env.example` to `.env` and set a random `SECRET_KEY`.
4. For a local SQLite demo, keep `DATABASE_URL=sqlite+aiosqlite:///./dps.db` and install `aiosqlite`.
5. Run `alembic upgrade head`.
6. Start API with `uvicorn app.main:app --reload`.
7. Start worker with `python -m app.workers.runner`.

## PostgreSQL deployment
Use `postgresql+asyncpg://...` and run migrations before starting the application. Set `AUTO_CREATE_SCHEMA=false` so production schema is migration-controlled.

## AI
Set `TRANSCRIPTION_PROVIDER=faster-whisper` and install the optional AI dependency after selecting hardware. Set `SUMMARIZATION_PROVIDER=ollama` and configure the local Ollama service. The deterministic providers exist only for automated tests.

## Production rules
- HTTPS is required.
- PostgreSQL must not be public.
- Audio storage must remain private.
- Use a dedicated worker process for AI jobs.
- Replace the local storage adapter with private S3-compatible storage when scaling beyond one machine.
- Rotate secrets and disable demo credentials.
- Set `EXPOSE_DEMO_RESET_TOKEN=false`.
- Review consent, retention and access policies with DPS before real student data is introduced.
