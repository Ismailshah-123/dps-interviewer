# V18 Demo Deployment

V18 is the demo deployment bundle for the DPS AI Student Interview System. It runs PostgreSQL, an Alembic migration job, the FastAPI backend, and the durable processing worker. Groq is configured as the demo AI provider through environment variables.

## Requirements

- Docker Engine with Docker Compose
- A Groq API key for live transcription and summarization
- A consented demo interview recording

## Start

1. Copy `.env.demo.example` to `.env`.
2. Set `SECRET_KEY`, `DEFAULT_ADMIN_PASSWORD`, and `GROQ_API_KEY`.
3. Run `./scripts/demo_up.sh`.
4. Open `http://localhost:8000/docs`.
5. Check `GET /api/v1/health/ready` and `GET /api/v1/health/ai`.

The migration service runs `alembic upgrade head` before the backend and worker start. The backend seeds the initial administrator and demo template after the schema exists; it does not create database tables when `AUTO_CREATE_SCHEMA=false`.

## Stop

Run `./scripts/demo_down.sh`.

The default command does not remove named volumes. To destroy demo data intentionally, run `docker compose -f docker-compose.demo.yml down -v`.

## Live AI smoke test

After the backend is running and a local Python environment has the project dependencies installed:

```text
GROQ_API_KEY=... python scripts/groq_demo_smoke.py ./demo-interview.wav
```

The smoke test consumes Groq inference quota. Use only a recording for which the participants have provided the required consent.

## Demo flow

Login as the seeded administrator, create a candidate, create an interview, confirm recording consent, upload a recording, and let the worker process the transcription and summary. Then inspect the transcript, AI draft, DPS form, review workflow, finalization, and PDF export.

## Security notes

- Never commit `.env`.
- Never expose `GROQ_API_KEY` to the browser.
- Replace all demo credentials before any public deployment.
- Do not use real student recordings in an unapproved external AI environment.
- Groq requests send audio/transcript data outside the local infrastructure; this must be approved by the applicable privacy/data policy.
