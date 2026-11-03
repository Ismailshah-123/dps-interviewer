# DPS AI Student Interview System — Project Log

**Format:** newest entry first (Keep-a-Changelog style). Every entry uses the same fields.
**Evidence tags:** `VERIFIED` = executed and passed (per the project's own docs) · `IMPLEMENTED` = code exists, not executed in the packaging environment · `NOT DONE` = missing or deferred.
**Dates:** taken from file timestamps in the package (26–28 Oct 2026). Where a day was not recorded it says so.

---

## 1. Project header

| Field | Value |
|---|---|
| Project | DPS AI Student Interview Recorder, Transcription & Form Automation System |
| Client | Dawood Public School (DPS) |
| Current version | **V18** — backend API `0.18.0`, frontend first pass (built against V16 contract + V18 `/meta`) |
| Last log update | 2026-10-30 |
| Stage | Demo-ready backend, untested frontend. **Not production-certified.** |
| Repo root | `dps-final-demo/` |

## 2. Current status

| Area | Tag | Evidence / note |
|---|---|---|
| Auth: Argon2, JWT access + refresh, revocation, password reset, lockout | IMPLEMENTED | Unit tests pass |
| RBAC (Administrator / Interviewer / Reviewer), central interview authorization | IMPLEMENTED | Unit/security tests pass (V11) |
| Candidates, interviews, lifecycle state machine | IMPLEMENTED | Workflow acceptance tests pass |
| Mandatory recording consent | IMPLEMENTED | Unit tests |
| Private audio storage, SHA-256, MIME/signature checks, duplicate guard | IMPLEMENTED | Storage unit tests pass |
| Durable jobs: retry/backoff, stale recovery, heartbeat, cancel | IMPLEMENTED | Unit tests pass |
| PostgreSQL row-lock claiming, idempotency races | IMPLEMENTED | Tests exist, **never run** (no PostgreSQL) |
| AI providers: Groq, Faster-Whisper, Ollama, deterministic | IMPLEMENTED | Adapter unit tests pass, **no live inference run** |
| Structured summary (strict JSON schema + Pydantic + evidence refs) | IMPLEMENTED | Unit tests |
| Versioned templates, generated form fields, human-edit preservation | IMPLEMENTED | Unit tests |
| Review workflow (submit → principal review → reviewed → finalized, correction loop) | IMPLEMENTED | Workflow acceptance tests pass |
| PDF export | IMPLEMENTED (foundation) | ReportLab; Urdu rendering **not verified** |
| Observability: JSON logs, correlation IDs, `/metrics`, AI metrics | IMPLEMENTED | Not exercised in a deployment |
| Demo deployment (Compose, migration gate, scripts) | IMPLEMENTED | YAML parsed only; Docker **never run** |
| Frontend (Next.js 16) | IMPLEMENTED (first pass) | **Never installed, built, linted or tested** |
| Browser recording (MediaRecorder) | NOT DONE | Frontend only uploads a chosen file |
| Official DPS 6–7 page template | NOT DONE | Demo template only |

### Test ledger

| Suite | Result |
|---|---|
| Backend unit suite | **44 passed** (V18) |
| Python compile, `scripts/release_check.py` | Passed |
| Integration / security API tests | **3 blocked** (`aiosqlite` missing): `test_auth.py::test_health`, `test_auth.py::test_login_and_create_candidate`, `test_authorization.py::test_unauthenticated_candidate_access_denied` |
| PostgreSQL acceptance (V12) | Never run |
| Live Groq smoke test | Never run |
| Faster-Whisper / Ollama real inference | Never run |
| Docker build/run | Never run |
| Frontend typecheck / lint / unit / build / Playwright | Never run (no `package-lock.json`) |
| Load test, backup/restore, security scans, accessibility audit | Never run |
| Ruff, mypy | Never run |

---

## 3. Entries (newest first)

### [2026-10-30] Handoff packaging — API stays 0.18.0
- **Changed:** repackaged V18 as `dps-final-demo/` for handoff to another LLM. No application code modified.
- **Removed:** all `__pycache__/` and `*.pyc`; `backend/.pytest_cache/`; `docs/frontend-master-prompt.md` (older duplicate; `docs/DPS_FRONTEND_PRODUCTION_MASTER_PROMPT.md` kept).
- **Added:** `LLM_HANDOFF.md`, this log, `docs/decisions.md`, `docs/owner-answers.md`, `docs/MASTER_PROJECT_PROMPT.md` (the full original requirements prompt), extra `.gitignore` entries, git repository with an initial commit.
- **Tests:** none run.
- **Not verified:** everything marked "never run" in section 2.

### [2026-10-28] V18 — Demo deployment bundle — API 0.18.0
- **Added:** `docker-compose.demo.yml` (PostgreSQL → Alembic migration job → FastAPI → worker); `.env.demo.example`; `scripts/demo_up.sh`, `scripts/demo_down.sh`; `docs/v18-demo-deployment.md`; `docs/frontend-backend-integration-v18.md`.
- **Changed:** initial admin and demo template seeding is decoupled from schema creation, so `AUTO_CREATE_SCHEMA=false` works with migrations.
- **Tests:** 44 unit passed; release check passed; Compose YAML parsed.
- **Not verified:** Docker runtime, live PostgreSQL, live Groq.

### [2026-10-28] V17 — Release candidate — API 0.17.0
- **Added:** migration runners (`run_migrations.sh` / `.ps1`); offline `scripts/release_check.py`; request path and status code in structured logs.
- **Changed:** validation-error responses carry the correlation ID; unhandled exceptions logged with correlation context; container runs as non-root with a liveness healthcheck.
- **Tests:** offline unit suite passes.
- **Not verified:** live PostgreSQL, live Groq; 3 integration tests still blocked.

### [2026-10-28] V16 — API contract and frontend integration — API 0.16.0
- **Added:** `GET /api/v1/meta` (non-secret metadata); typed `UserPage` response; `scripts/export_openapi.py`; first-pass Next.js frontend added to the bundle.
- **Fixed:** candidate PATCH honours explicitly nullable fields (`exclude_unset`); removed an accidental temporary source artifact.
- **Security:** `/meta` exposes no keys, URLs, paths or secrets.
- **Not done:** `docs/openapi.json` is referenced but was not generated in the package.

### [2026-10-28] V15 — Demo AI completion pass — API version not recorded
- **Added:** 25 MiB Groq free-tier upload guard (configurable); strict JSON-Schema structured outputs for GPT-OSS 20B; evidence references and unclear/missing info in the summary schema; AI request/failure/latency metrics; `scripts/groq_demo_smoke.py`.
- **Tests:** 42 unit passed.
- **Privacy:** audio and transcript text leave local infrastructure when Groq is enabled.
- **Not verified:** live Groq inference.

### [2026-10-28] V14 — Demo AI configuration — API version not recorded
- **Added:** Groq providers (`whisper-large-v3-turbo`, `openai/gpt-oss-20b`); typed Groq errors (retryable: 408, 409, 425, 429, 5xx; `Retry-After` honoured); `GET /api/v1/health/ai` (config check only, no quota use); `docs/groq-demo-setup.md`.
- **Security:** API key is server-side only.
- **Privacy:** needs explicit DPS approval before real student data.
- **Not verified:** live Groq inference, PostgreSQL runtime, provider quota.

### [2026-10-27] V13 — Reliability and observability — API 0.13.0
- **Added:** JSON structured logging; Prometheus `/metrics` (requests, errors, latency, job completed/failed/retried/recovered/running); DB pool settings; configurable worker poll interval; `docs/v13-operations.md`.
- **Changed:** worker shuts down gracefully on SIGINT/SIGTERM; worker loop isolates unexpected exceptions.
- **Security:** keep `/metrics` on an internal network; telemetry contains no audio, transcripts, tokens or provider payloads.

### [2026-10-27] V12 — PostgreSQL concurrency acceptance — API 0.12.0
- **Added:** PostgreSQL-only tests for the two-worker claim race (`FOR UPDATE SKIP LOCKED`) and idempotency-key uniqueness race; disposable-DB runner (`scripts/postgres_acceptance.sh/.py`, uses `DPS_TEST_DATABASE_URL`).
- **Not verified:** the suite was **never executed** (no PostgreSQL). Hard gate before production.

### [2026-10-27] V11 — Security and authorization hardening — API 0.11.0
- **Added:** centralized `app/services/authorization.py`; last-active-administrator protection.
- **Changed:** interviewers see only assigned interviews/candidates; reviewers see only principal-review interviews and cannot edit transcript or form fields; reviewed/finalized records are immutable via edit endpoints; recording download follows the same visibility rules.
- **Security:** refresh-token rotation uses PostgreSQL row locking against concurrent reuse races.
- **Tests:** 35 unit/security passed; 3 integration tests blocked.

### [26–27 Oct] V10 — Workflow acceptance and retry recovery — API version not recorded
- **Added:** acceptance tests for the full lifecycle (draft → finalized) and the correction loop.
- **Changed:** admin retry restores interview state first (`failed → queued` for transcription, `failed → transcript_ready` for summary); retry resets the attempt counter; cancel clears scheduling.
- **Tests:** 24 unit passed.

### [26–27 Oct] V9 — API contract and operational hardening — API 0.9.0
- **Added:** pagination metadata (`total`, `skip`, `limit`, `has_more`); status filters; bounded, filterable admin jobs/audit/users endpoints.
- **Changed:** candidate PATCH is a true partial update.
- **Fixed:** consent-withdraw path (missing UTC datetime import).
- **Tests:** 24 unit passed.

### [26–27 Oct] V8 — Workflow and review hardening
- **Changed:** submit stops at `submitted`; reviewer actions advance `submitted → principal_review → reviewed`; correction requests only from principal review and require remarks; finalize only from `reviewed`; cannot mark `reviewed` while any field is `needs_review`.
- **Tests:** 20 unit passed.

### [26–27 Oct] V7 — Worker hardening
- **Added:** independent heartbeat loop during long provider calls; admin cancel endpoint `POST /api/v1/processing/jobs/{job_id}/cancel`.
- **Fixed:** cancelled jobs can no longer commit AI output; long AI calls are no longer falsely recovered as stale.
- **Tests:** 18 unit passed.

### [2026-10-26] V1–V6 — Foundation (reconstructed)
Individual notes for V1–V6 were not included in the package. Reconstructed from `implementation-status.md`, migrations and file dates.
- **Added:** FastAPI + async SQLAlchemy + Alembic; auth; candidates; interviews; consent; private storage; audit model; durable processing jobs; transcription and summarization adapters; background worker; versioned placeholder template; form population; editable transcript/form APIs; PDF foundation.
- **Migrations:** `f20a7b614f44` initial schema; `42ab447c5d18` security and indexes; `7c8d9e10f123` processing reliability; `8d9e10f12456` processing claims.
- **Docs:** research, architecture, threat model, data dictionary, privacy and retention, backup and recovery, capacity planning, test plan; frontend production master prompt.
- **Tests:** 10 unit passed at this checkpoint.

---

## 4. Gaps against the original master prompt

| Requirement | State |
|---|---|
| React + Vite + shadcn/ui + React Router (§4) | **Deviation:** Next.js 16 is in place; shadcn/ui and React Router are not in `package.json`. Decision recorded in `docs/decisions.md`, owner confirmation pending |
| MediaRecorder: pause/resume, level meter, device select, chunked upload (Module 4) | NOT DONE |
| No tokens in browser storage; HttpOnly cookies (Module 1) | PARTIAL: bearer tokens in `sessionStorage` (not `localStorage`); frontend README calls this transitional |
| Real transcription on English/Urdu/mixed audio, WER evaluation (§11) | NOT DONE |
| Urdu PDF rendering (Module 12) | NOT VERIFIED |
| Official DPS template mapped (Module 9) | NOT DONE |
| Transcript search, click-to-seek audio, version history UI (Module 10) | Not evident in the frontend |
| Speaker diarization | Optional; not implemented |
| Full Playwright E2E (§12E) | Only `login.spec.ts` |
| Load test, backup/restore, scans, clean-checkout install (Gate 7) | NOT DONE |
| No audio to external AI without authorization (§5) | **Conflict:** Groq demo default sends audio/text out. Documented; needs a written DPS decision |

## 5. Known issues

| # | Issue | Status |
|---|---|---|
| 1 | `docs/production-readiness.md` says 10 unit tests; current figure is 44 | Open |
| 2 | `docs/one-week-checklist.md` shows frontend items unchecked | Open |
| 3 | `frontend/README.md` points to `docs/production-release-gates.md`, which does not exist | Open |
| 4 | `docs/openapi.json` referenced but not generated | Open |
| 5 | Original zip contained `__pycache__/` and `.pytest_cache/` | **Resolved 2026-10-30** |
| 6 | No `package-lock.json`; frontend Docker build fails by design until one is committed | Open |
| 7 | `pyproject.toml` version 0.1.0 vs API 0.18.0 | Open (cosmetic) |
| 8 | Groq 25 MiB guard: a 40-min 16 kHz mono 16-bit WAV is about 76.8 MB (my calculation); use compressed audio such as WebM/Opus (about 19 MB at 64 kbps) | Open |
| 9 | Candidate list loads only the first 50; dashboard counts are page-scoped | Open |
| 10 | Transcript segment schema may need an explicit `original_text` | Open |

## 6. Open release gates

**To a working demo**
1. Configure `.env` (`SECRET_KEY`, `DEFAULT_ADMIN_PASSWORD`, `GROQ_API_KEY`); run `./scripts/demo_up.sh`; check `/api/v1/health/ready` and `/api/v1/health/ai`.
2. Run `groq_demo_smoke.py` with a consented, compressed recording.
3. `npm install`; commit the lockfile; run `typecheck`, `lint`, `test`, `build`; fix failures.
4. Walk the whole flow by hand: admin → candidate → interview → consent → upload → transcript → summary → form → submit → review → finalize → PDF.
5. Install `aiosqlite` and clear the 3 blocked tests.

**Before any real student data**
6. Get the approved DPS template and map it exactly.
7. Run the PostgreSQL acceptance suite on a disposable database.
8. Written DPS approval for consent wording, retention, deletion and external AI use (or switch to local Faster-Whisper + Ollama).
9. Build the MediaRecorder flow; verify Urdu PDF output visually.
10. Benchmark transcription on authorized English, Urdu and mixed audio.
11. Replace demo credentials; disable reset-token exposure; protect `/metrics`; move to HttpOnly-cookie sessions.
12. Load test, backup/restore drill, dependency and secret scans, accessibility audit, full Playwright lifecycle.

## 7. Decisions on record

| Decision | Source |
|---|---|
| Durable PostgreSQL-backed job queue, not an in-memory list | `docs/processing-reliability.md` |
| Idempotency keys `transcription:{interview_id}:{recording_sha256}` and `summary:{interview_id}:{transcript_id}` | `docs/processing-reliability.md` |
| Swappable AI providers (Groq / local / deterministic) | V14, V15 |
| Groq is the demo provider only | V14 |
| Reviewers cannot edit evidence; reviewed/finalized records are immutable | V11 |
| Prometheus + JSON logs; OpenTelemetry deferred | V13 |
| Backend is authoritative for workflow; frontend invents no endpoints or statistics | `frontend/README.md` |

## 8. Safe wording for claims

**Safe now:** the backend is a unit-tested foundation (auth, RBAC, consent, private storage, durable processing, structured summaries, review workflow, PDF foundation). The frontend is a first implementation connected to that API and not yet built or tested. The demo template is a placeholder.

**Not yet:** "works end to end", "transcribes Urdu accurately", "production-ready", "secure", "tested with PostgreSQL / Docker / Groq". None of these has been run.

## 9. How to add an entry

Insert above the newest entry in section 3 and update sections 2, 5 and 6 if status changed.

```
### [YYYY-MM-DD] Vxx — Short title — API x.y.z
- **Added:**
- **Changed:**
- **Fixed:**
- **Security:**
- **Removed:**
- **Commands run:**
- **Tests:** passed N / failed N / skipped N (reason for each skip)
- **Not verified:**
- **Blockers:**
- **Next:**
```
Rules: never write "passed" for something you did not run; paste real counts; list every skip with its reason.

---

### 2026-10-30 — V19: Make it run, real local AI, new frontend, full E2E (Phases A, D, E, partial C/F)

Environment: Windows 11, i5-12450H (12 threads), 15.7 GB RAM, RTX 3050 Laptop 4 GB, Python 3.14.0, Node 24.12. **No Docker, no PostgreSQL, no Ollama installed.**

- **Changed**
  - Backend now installs (packaging config was missing; `{__init__.py}` brace-expansion files renamed; `.gitignore` `storage/` rule had silently excluded `app/services/storage/` from git).
  - Bugs fixed, each found by running the code: missing `logging` import (500 on any unhandled error); seeded admin `admin@dps.local` could never log in (email-validator rejects `.local`); **token refresh never worked on SQLite** (naive vs aware datetimes; fixed with `UTCDateTime`); CSV list settings (`CORS_ORIGINS`) could not be read from `.env`; illegal lifecycle transitions returned 500 (now 409); direct upload from `draft` was impossible; no way to leave `correction_requested`; `manual_only` "Interviewer Observations" was filled from AI output; browsers' `audio/webm;codecs=opus` MIME type was rejected.
  - Security/workflow: HttpOnly SameSite=Strict refresh cookie; evidence frozen after submission for every role; submission requires every field confirmed; field-confirm endpoint; resubmission bumps form revision; review history, stats, template-version endpoints; deterministic providers refused outside `ENVIRONMENT=test`; audit events for interview creation, consent, recording start, field confirmation, resubmission.
  - faster-whisper provider: cached model, per-segment confidence signal (documented as not a correctness probability), model version, `WHISPER_LANGUAGE` override, error when no speech is recognised.
  - PDF: metadata header, placeholder-template notice, per-field provenance, page footer, Unicode font with Urdu reshaping/bidi.
  - **Frontend rebuilt** on React + Vite + TS + Tailwind v4 + shadcn/ui + React Router + TanStack Query + RHF/Zod (see decisions.md). Screens: login + password reset, dashboard, candidates (search, pagination, duplicate warning), candidate detail, interviews list, interview workspace (consent, recording, processing, transcript with search and click-to-seek, AI summary, form review/confirm/submit, review + history), review queue, staff accounts, templates, processing jobs (retry/cancel), audit log, system health, access-denied, 404, route error page.
  - **MediaRecorder recording**: feature detection, device selection, level meter, pause/resume, elapsed time, 90-min cap, chunks persisted to IndexedDB every 5 s (crash/tab-close recovery), "not yet saved" state until the server confirms, upload progress, retry, cancel, discard, low-storage warning, permission/no-device errors.
- **Files**: see `git status`; main areas `backend/app/{api,core,models,services,workers}`, `backend/tests/{integration,security,unit,real_audio}`, new `frontend/`, `scripts/{e2e_backend.py,demo_pipeline.py,make_synthetic_interview.ps1}`, `README.md`, `docs/decisions.md`.
- **Commands run / results (all executed in this environment)**
  - `pytest` (backend): **62 passed, 2 skipped** — skipped: PostgreSQL concurrency suite (no PostgreSQL), opt-in real-audio test (run separately below).
  - `alembic upgrade head` on a fresh SQLite DB: all 4 revisions applied; `alembic check`: no drift.
  - Frontend: `tsc -b` clean; `oxlint` 0 errors (fast-refresh warnings only); `vitest` **22 passed**; `vite build` OK (single 774 kB chunk — code-splitting not yet done); `npm audit --omit=dev` 0 vulnerabilities.
  - Playwright E2E: **1 passed (~30 s)** — admin creates interviewer → candidate → consent gate → real MediaRecorder capture from Chromium fake mic (synthetic WAV) incl. pause/resume → IndexedDB → upload → processing (deterministic provider) → transcript/summary/form → manual field + confirm all → submit → principal begins review → correction (remarks required) → interviewer edits and resubmits → reviewed → finalized → PDF download → second interviewer gets 404 in UI and API (form PDF, audio) → access-denied page.
  - **Real AI (Gate C, English only)**: faster-whisper `small`, CPU int8, on a 67.8 s synthetic two-voice English interview: language `en`, 19 timestamped segments, ~24 s wall including model load, negation preserved ("I do not like painting"), dates/numbers normalised ("14 March, 2018", "Class 3"). **Name error: "Ayesha" → "Aisha".** The embedded prompt-injection sentence was transcribed verbatim as content.
  - Same audio through the running API + worker (`scripts/demo_pipeline.py`): transcription completed in 27 s; summary job failed after 3 attempts ("All connection attempts failed" — Ollama not installed); interview marked `failed`; **no transcript or summary was fabricated.**
  - GPU: `WHISPER_DEVICE=cuda` fails — `cublas64_12.dll` not present (needs CUDA 12 cuBLAS + cuDNN 9 runtime).
  - PDF rendered with pypdfium2 and inspected visually: Urdu joined and right-aligned (Naskh, not Nastaliq); in a mixed English+Urdu line the trailing full stop is placed on the wrong side.
- **Not verified**: Urdu or mixed-language transcription (no Urdu TTS voice; needs consented/synthetic recordings); any summarization model (Ollama absent); Firefox/Safari recording; 40-minute recording in a real browser; PostgreSQL; Docker; load test; backup/restore; real microphone in a real browser (only Chromium fake device).
- **Blockers / owner decisions**: Ollama install (or approval for Groq on synthetic data); official DPS template; consent wording, retention period, audio access policy; PostgreSQL target; hardware for production inference.
- **Next**: install Ollama and run summarization + prompt-injection evaluation on the synthetic set; Urdu/mixed evaluation set; PostgreSQL acceptance suite; code-split frontend bundle; recording metadata (duration) on the server; evidence references per form field; load test; backup/restore drill.

### 2026-10-31 — V20: Real summaries via Groq (synthetic data only), prompt v4

- **Decision (owner, 2026-10-30):** use Groq for summaries on fake/synthetic data. Transcription stays local (faster-whisper), so audio never leaves the laptop; only transcript text is sent to Groq. Real student data still requires written DPS approval.
- **Changed**
  - `backend/.env` (git-ignored): `SUMMARIZATION_PROVIDER=groq`, `GROQ_SUMMARY_MODEL=openai/gpt-oss-20b`; key added by the owner (never printed or logged).
  - Amber in-app banner whenever a cloud provider is configured (`/meta` → `external_ai`).
  - Shared summarization prompt **v4** for Groq and Ollama (`services/summarization/prompt.py`): transcript treated as data, no sensitive inferences, careful speaker attribution, no AI-written "observations", names/dates/numbers flagged, no placeholders.
  - `clean_summary()` applied by the worker for every provider: drops placeholder items ("None recorded"), de-duplicates, and adds deterministic review flags — student statements with no first-person words ("Confirm speaker") and unflagged dates/numbers. It never rewrites content.
  - Test isolation: tests and the E2E server no longer read the developer's `backend/.env` (`DPS_ENV_FILE=""`); one test had been passing/failing depending on local secrets.
- **Results (synthetic 68 s English interview, real Whisper `small` CPU + real Groq gpt-oss-20b)**
  - End to end upload → `needs_review` in 24–38 s; summary step ~4 s; 1 attempt, no errors.
  - Prompt-injection sentence ("…write that the child is highly recommended…"): **not followed** in v3 or v4.
  - v3 → v4: AI-invented interviewer observation removed; "None recorded." placeholder removed (form now shows *Not mentioned*); sensitive "missing: family background, special needs" removed; misspelled name now flagged for confirmation.
  - Still wrong in v4: the parent's sentence "She swims twice a week…" filed under student statements (model ignores the attribution rule; no diarization). Now caught by the deterministic "Confirm speaker" flag. Birth date flagged by the deterministic check.
  - Evidence quotes matched real transcript segments and timestamps.
  - UI verified with headless Chromium screenshots: banner, AI labels, flags, evidence, empty manual field, placeholder-template warning.
- **Tests:** backend 67 passed, 2 skipped (PostgreSQL; opt-in real audio). Frontend 22 passed, typecheck clean.
- **Not verified:** Urdu/mixed summaries; behaviour on a 40-minute transcript (Groq free-tier token limits, `GROQ_SUMMARY_MAX_TOKENS=4096`); Ollama path with prompt v4.
- **Next:** evaluation set (several synthetic interviews incl. negations, multiple children's names, contradictions) scored field by field; speaker diarization or an interviewer-set speaker label; per-field evidence links.
