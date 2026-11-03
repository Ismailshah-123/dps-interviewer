# Production Readiness

Status: **Backend foundation complete for the currently available specification; production deployment is not yet certified.**

## Implemented in the current checkpoint

- Authentication with Argon2, JWT access and refresh tokens
- Refresh-session revocation and password reset workflow
- Server-side RBAC
- Candidate/interview ownership controls
- Consent persistence
- Private recording storage
- SHA-256 recording checksum and duplicate detection
- Audio size, declared MIME and basic media-signature validation
- Idempotent processing jobs
- Retry limits and bounded exponential backoff
- Durable `next_attempt_at` scheduling
- Worker claim timestamps and heartbeat timestamps
- Stale running-job recovery after worker crashes
- PostgreSQL `FOR UPDATE SKIP LOCKED` job claiming
- Transcript persistence with original text and editable segments
- Structured deterministic and pluggable AI providers
- Versioned templates and human-reviewable generated form fields
- Review/correction/finalization workflow
- Audit events
- Retention purge foundation
- Admin job retry endpoint
- Alembic migration chain through processing reliability and worker-claim fields
- Unit test suite: 10 tests passing in the available environment

## Verification boundary

Verified here:

- Python compilation passes.
- Unit tests pass: 10/10.
- Storage traversal and basic audio-signature validation tests pass.
- Processing retry policy tests pass.

Not verified here because the required infrastructure or packages are unavailable:

- Full HTTP integration/security suite using `aiosqlite`.
- Real PostgreSQL migration execution.
- Docker image build and multi-process deployment.
- Faster-Whisper model inference.
- Ollama model inference.
- Load/concurrency testing.
- Production object storage.
- Backup restore drills.
- Formal security scanning.
- Browser/E2E testing.
- Official DPS 6-7 page template fidelity.

These items are deliberately not represented as successful tests.

## Remaining release gates

1. Obtain the approved DPS interview template and implement its exact field/page mapping.
2. Install and validate `aiosqlite` for the local integration suite or run integration tests against PostgreSQL.
3. Deploy a staging PostgreSQL instance and execute `alembic upgrade head` plus rollback validation.
4. Install and benchmark Faster-Whisper using representative authorized English, Urdu and mixed-language recordings.
5. Configure and validate Ollama with the selected local model and evidence-grounded prompt contract.
6. Replace local storage with private object storage for multi-instance deployments.
7. Add centralized metrics, structured logs, alerting and worker health monitoring.
8. Execute load, security, backup/restore and browser E2E test plans.
9. Disable demo credentials and reset-token exposure before any real student data is processed.
10. Approve consent, retention, deletion and legal-hold policies with DPS.

## V12 database gate

Before production approval, run the PostgreSQL acceptance suite against a disposable PostgreSQL instance and require all V12 tests to pass. This is a hard gate for worker concurrency and processing idempotency.
