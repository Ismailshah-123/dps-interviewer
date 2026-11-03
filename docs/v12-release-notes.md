# V12 Release Notes

## PostgreSQL Production Integration and Concurrency Acceptance

V12 establishes the production database acceptance layer for PostgreSQL-backed execution.

### Implemented

- PostgreSQL-only concurrency acceptance tests.
- Two-worker processing claim race test using `FOR UPDATE SKIP LOCKED`.
- Processing-job idempotency uniqueness race test.
- Disposable-database acceptance runner using `DPS_TEST_DATABASE_URL`.
- PostgreSQL migration execution is explicitly separated from application startup validation.
- API version advanced to `0.12.0`.

### Concurrency contract

A worker must claim a queued processing job inside its own database transaction. PostgreSQL row locking with `SKIP LOCKED` allows competing workers to skip already-claimed rows rather than waiting on the same queue item. The claim transaction commits before provider work begins.

Each concurrent asyncio task uses its own `AsyncSession`; sessions are not shared across tasks.

### Required real-environment validation

The execution environment used to package V12 does not provide a PostgreSQL server or Docker. Therefore the PostgreSQL acceptance suite is included but is not represented as passed here.

Run against a disposable PostgreSQL database:

```text
export DPS_TEST_DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dps_test
./scripts/postgres_acceptance.sh
```

The suite must report all PostgreSQL tests passing before production approval.

### Explicit limitations

- No claim is made that real PostgreSQL concurrency passed in the packaging environment.
- AI provider inference is not part of V12 database acceptance.
- The official DPS paper form is still not an exact production template until the real source template is supplied.
