# DPS AI Student Interview Documentation System

**A human-reviewed workflow for recording, transcribing, and documenting student admission interviews.**

The system captures an interview with consent, creates a transcript and structured draft, and routes the record through interviewer confirmation and principal review. **Staff remain responsible for every field; the software does not make, rank, or recommend admission decisions.**

> **Current status:** End-to-end demonstration using synthetic data. Not production-ready. The interview form remains a placeholder pending the official school template. Verification notes are maintained in `docs/PROJECT_LOG.md`.

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, TypeScript (strict), Tailwind CSS v4, shadcn/ui (Radix), React Router 7, TanStack Query 5, React Hook Form + Zod, Lucide, Sonner |
| Backend | Python 3.11–3.14, FastAPI, Pydantic 2, SQLAlchemy 2 (async), Alembic, Argon2id, PyJWT, ReportLab |
| Database | SQLite for the single-machine demo; PostgreSQL (asyncpg) for production |
| AI (local, free) | faster-whisper (Whisper `small` by default) for speech-to-text; Ollama for structured summaries |
| Tests | pytest + HTTPX, Vitest + Testing Library, Playwright (Chromium with a fake microphone) |

## Quick start (Windows, local demo)

Prerequisites: Python 3.11+, Node 20+, ffmpeg (for the synthetic sample), and optionally [Ollama](https://ollama.com) for summaries.

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev,ai]"
```

Create `backend/.env` (it is git-ignored). Minimum:

```text
ENVIRONMENT=development
SECRET_KEY=<at least 32 random characters>
DATABASE_URL=sqlite+aiosqlite:///./dps_demo.db
DEFAULT_ADMIN_EMAIL=admin@dps.example.com
DEFAULT_ADMIN_PASSWORD=<choose one>
TRANSCRIPTION_PROVIDER=faster-whisper
WHISPER_MODEL=small
SUMMARIZATION_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:3b
```

Run three processes (three terminals):

```bash
cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000
```

```bash
cd backend && .venv/Scripts/python -m app.workers.runner
```

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 and sign in with the admin account from `.env`. The Vite dev server proxies `/api` to FastAPI, so the HttpOnly session cookie works without CORS.

For summaries, install Ollama, then pull the model named in `OLLAMA_MODEL`:

```bash
ollama pull qwen2.5:3b
```

Without Ollama, transcription still works and the summary job fails with a clear error. Nothing is invented.

### Synthetic sample interview

```bash
powershell -File scripts/make_synthetic_interview.ps1
```

```bash
backend/.venv/Scripts/python scripts/demo_pipeline.py
```

The first script creates a two-voice English interview with Windows text-to-speech. The second pushes it through the running API and worker with the configured real providers. No real student data is involved.

## Tests

```bash
cd backend && .venv/Scripts/python -m pytest -q
```

```bash
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
```

```bash
cd frontend && npx playwright install chromium && npm run test:e2e
```

The E2E suite starts its own isolated backend (`scripts/e2e_backend.py`, `ENVIRONMENT=test`, deterministic AI providers, fresh database) and drives the whole interviewer-to-principal workflow, including real browser recording from a fake microphone.

Opt-in real-model test (downloads Whisper weights on first run):

```bash
cd backend && DPS_REAL_AUDIO=1 .venv/Scripts/python -m pytest tests/real_audio -s
```

## Safety properties enforced in code

- Authorization is checked by the backend on every endpoint, download and export; other users' records return 404.
- Recording and upload are refused until consent is recorded (notice version, staff account, time).
- Evidence (transcript and form) can only be edited before submission or during a requested correction.
- Submission requires the interviewer to confirm or edit every field; "Interviewer Observations" is never AI-filled.
- Deterministic test providers are refused unless `ENVIRONMENT=test`, so a demo cannot show canned AI output.
- Refresh tokens live in an HttpOnly, SameSite=Strict cookie; access tokens are kept only in memory.
- Audio is stored privately with a SHA-256 checksum and served only through authorized requests.

## Documentation

`docs/PROJECT_LOG.md` (status and verified results), `docs/decisions.md`, `docs/architecture.md`, `docs/threat-model.md`, `docs/privacy-and-retention.md`, `docs/deployment.md`, `docs/production-readiness.md`.
