# Decisions Log

Record every change to the stack, API contract, data model or security approach here.
Format: date, decision, reason, alternatives rejected, files affected.

| Date | Decision | Reason | Alternatives | Files affected |
|---|---|---|---|---|
| 2026-10-30 | Keep Next.js 16 frontend (original master prompt said React + Vite + shadcn/ui) | Frontend already built on Next.js (see DPS_FRONTEND_PRODUCTION_MASTER_PROMPT.md); confirm with owner | React + Vite | frontend/ |
| 2026-10-30 | **Frontend rebuilt on React + Vite + shadcn/ui + React Router** (supersedes the Next.js row above) | The master prompt specifies this stack; the Next.js code was minified one-line files that failed typecheck, lint and its own tests, and lacked MediaRecorder, shadcn/ui and React Router | Repair the Next.js app | `frontend/` (old code remains in git history) |
| 2026-10-30 | Refresh token in HttpOnly SameSite=Strict cookie scoped to `/api/v1/auth`; access token in memory only; logout works without a valid access token | Master prompt forbids tokens in browser storage; the old frontend used sessionStorage | BFF session store | `backend/app/api/auth.py`, `frontend/src/lib/api.ts` |
| 2026-10-30 | Evidence editable only in `transcript_ready`, `form_draft_ready`, `needs_review`, `correction_requested` for all roles (admins included) | Prevents silent edits after submission; audit trail stays meaningful | Admin override | `services/authorization.py` |
| 2026-10-30 | Submit requires every field confirmed or edited; new `POST /forms/{id}/fields/{field}/confirm` keeps "human-confirmed" distinct from "human-edited" | Human review before finalization; previously the principal could be blocked by unreviewed fields | Re-PATCH same value | `api/interviews.py`, `api/forms.py` |
| 2026-10-30 | Correction loop: interviewer resubmits from `correction_requested`; form revision increments | No endpoint previously left `correction_requested` | Separate reopen endpoint | `api/interviews.py` |
| 2026-10-30 | `manual_only` template fields are never filled from AI output | Spec: never fabricate interviewer observations | — | `workers/processor.py` |
| 2026-10-30 | `deterministic-test` providers refused unless `ENVIRONMENT=test` | Canned text must never appear in a demo as real output | Docs warning only | `core/config.py` |
| 2026-10-30 | Lifecycle violations return HTTP 409 (`InvalidTransition`), not 500 | Correct semantics; draft→uploading allowed for direct file upload | — | `services/workflow.py`, `main.py` |
| 2026-10-30 | `UTCDateTime` column type | SQLite returns naive datetimes; refresh-token expiry comparison raised TypeError so refresh never worked on SQLite | Per-site fixes | `models/models.py` (no DDL change) |
| 2026-10-30 | New endpoints: `GET /interviews/stats`, `GET /reviews/{id}`, `GET /templates/versions/{id}`; interview rows carry candidate reference/name and consent status; list filter by `candidate_id` and multiple `status` | Dashboard counts must be system-wide; review history and template structure were not readable | Client-side joins | `api/*.py` |
| 2026-10-30 | Local default AI: faster-whisper `small` on CPU int8; Ollama `qwen2.5:3b` for summaries. (Superseded for the demo on 2026-10-31: Groq for summaries on synthetic data, Whisper stays local.) | Free, offline, no school audio leaves the machine | Groq default | `backend/.env` |
| 2026-10-30 | Python 3.14 accepted (`requires-python <3.15`); PyAV pinned `<17` | Only 3.14 is installed; faster-whisper 1.2.1 breaks with PyAV 17+ | Install 3.13 | `backend/pyproject.toml` |
| 2026-10-30 | PDF: Unicode font + arabic-reshaper + python-bidi for Urdu, metadata header, provenance line per field | Helvetica cannot render Urdu at all | HTML-to-PDF engine | `services/pdf/generator.py` |
| 2026-10-30 | Demo admin email `admin@dps.example.com` | `.local` is rejected by email-validator, so the seeded admin could never log in | — | config, `.env*.example` |
| 2026-10-31 | Demo summaries via Groq `openai/gpt-oss-20b`, synthetic data only; transcription stays local; in-app banner when any cloud AI is on | Owner choice; no Ollama installed; audio never leaves the laptop | Ollama (still supported; one-line switch) | `backend/.env`, `api/meta.py`, `AppShell.tsx` |
| 2026-10-31 | One shared prompt (v4) for all summarizers + deterministic `clean_summary` flags (speaker, dates/numbers, placeholders) that never rewrite content | Measured model errors on synthetic audio; flags keep humans in charge | Code that moves statements between fields | `services/summarization/prompt.py`, `workers/processor.py` |
