# Research and Architecture Decision Record

## 2026-10-26 research snapshot

### Speech recognition

The selected demo abstraction is provider-independent with a Faster-Whisper adapter. The current Faster-Whisper documentation describes it as a CTranslate2 implementation of Whisper and reports substantial speed and memory improvements versus the reference implementation. Its current release documentation also notes multilingual transcription and code-switching support in larger models. These facts support using it as a candidate local demo provider, but they do not establish production accuracy for DPS English/Urdu interviews. Accuracy must be measured on representative authorized or synthetic audio.

Source: https://github.com/SYSTRAN/faster-whisper

### Structured summarization

The summarization layer uses a provider adapter and an Ollama implementation. The implementation sends a Pydantic-generated JSON schema to Ollama so the response can be validated instead of treating free-form text as a reliable record. The prompt explicitly rejects unsupported inference and treats spoken instructions as interview content.

### Database

SQLAlchemy 2.x async support is selected for the FastAPI application. PostgreSQL is the production target and SQLite is intended only for local development/testing when the async SQLite driver is installed. SQLAlchemy documents async engine/session support and recommends explicit session handling rather than unsafe sharing of an AsyncSession between concurrent tasks.

Source: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

### Authentication

FastAPI's current security documentation supports signed JWT access tokens and secure password hashing patterns. The implementation uses Argon2id for password hashing and short-lived access tokens with server-tracked refresh sessions.

Source: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

## Decisions

1. Python/FastAPI is the authoritative backend.
2. PostgreSQL is the production database.
3. Private filesystem storage is the demo storage abstraction.
4. Audio is never stored as a database blob.
5. AI work is represented as durable processing jobs and handled outside request handlers.
6. AI providers are adapters so model providers can be replaced without changing API/domain code.
7. The official school template is not invented. A placeholder is seeded only to make the first demo vertical slice testable.
8. Human review is required before finalization.
9. The system does not generate autonomous admission decisions or scores.
