# V17 Release Candidate

## Scope

V17 is the backend release-candidate hardening pass. It does not claim live PostgreSQL or live Groq validation when those services are unavailable in the execution environment.

## Changes

- API version 0.17.0
- Explicit FastAPI validation-error responses include the correlation ID
- Unhandled request exceptions are logged with correlation context
- Production container runs as a non-root user
- Container has a liveness healthcheck
- Added migration runner scripts for Unix and PowerShell
- Added offline release-check script
- Expanded structured logs with request path and status code fields
- Added frontend metadata version update

## Release commands

```bash
python scripts/release_check.py
python -m compileall -q backend/app
cd backend && pytest -q tests/unit
```

For a real PostgreSQL environment:

```bash
./scripts/run_migrations.sh
```

Then run the PostgreSQL acceptance suite with `DPS_TEST_DATABASE_URL` configured.

For a real Groq demo, configure `GROQ_API_KEY`, enable the Groq providers, and run the demo smoke test from the scripts directory.

## Test truth

The offline unit suite passes in the current environment. Three integration tests remain environment-blocked because `aiosqlite` is unavailable. PostgreSQL and live Groq inference require their respective external runtimes and credentials and are not represented as passed by this release.
