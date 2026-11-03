# Test Plan

## Executed today

- Python compile check for application and Alembic files: passed.
- Workflow unit tests: 2 passed.
- Alembic autogeneration against SQLite sync inspection: completed successfully.

## Not executable in the current environment

API/database integration tests require `aiosqlite` for the local SQLite async configuration. The environment has no PostgreSQL client/server and no Docker, and package installation cannot reach the package index. These are environment blockers, not test passes.

## Required next gates

1. Install `aiosqlite`, `asyncpg`, pytest-asyncio and other project dependencies from a package mirror.
2. Run all unit and integration tests.
3. Run authorization regression tests.
4. Add deterministic fake transcription and summarization providers for API/E2E tests.
5. Add Playwright frontend tests.
6. Run real-model tests only in an explicit opt-in suite.
7. Run PDF extraction and visual checks.
8. Run load tests separately for API and AI workers.
