import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.models.models import User, InterviewTemplate, InterviewTemplateVersion, Role
from app.core.security import hash_password
from app.core.request_context import correlation_id
from app.services.workflow import InvalidTransition
from app.core.observability import configure_logging, request_started, request_failed, request_duration
from app.services.templates.default import DEFAULT_TEMPLATE_NAME, DEFAULT_TEMPLATE_DESCRIPTION, DEFAULT_FIELDS, DEFAULT_TEMPLATE_VERSION
from app.api import auth, candidates, interviews, recordings, processing, templates, transcripts, forms, reviews, admin, health, users, summaries, meta
from sqlalchemy import select

configure_logging()

async def seed_defaults():
    async with SessionLocal() as db:
        admin = await db.scalar(select(User).where(User.email == settings.default_admin_email.lower()))
        if not admin:
            admin = User(email=settings.default_admin_email.lower(), full_name="DPS Administrator", password_hash=hash_password(settings.default_admin_password), role=Role.ADMIN.value)
            db.add(admin)
        template = await db.scalar(select(InterviewTemplate).where(InterviewTemplate.name == DEFAULT_TEMPLATE_NAME))
        if not template:
            template = InterviewTemplate(name=DEFAULT_TEMPLATE_NAME, description=DEFAULT_TEMPLATE_DESCRIPTION, active=True)
            db.add(template)
            await db.flush()
        versions = (await db.scalars(select(InterviewTemplateVersion).where(InterviewTemplateVersion.template_id == template.id))).all()
        current = next((v for v in versions if v.version == DEFAULT_TEMPLATE_VERSION), None)
        for version in versions:
            version.is_current = version.version == DEFAULT_TEMPLATE_VERSION
        if not current:
            current = InterviewTemplateVersion(
                template_id=template.id,
                version=DEFAULT_TEMPLATE_VERSION,
                fields=DEFAULT_FIELDS,
                is_current=True,
            )
            db.add(current)
        else:
            current.fields = DEFAULT_FIELDS
            current.is_current = True
        template.description = DEFAULT_TEMPLATE_DESCRIPTION
        template.active = True
        await db.commit()

async def run_inline_worker():
    """Run the PostgreSQL-backed job queue in this API process for small demos."""
    logger = logging.getLogger(__name__)

    from app.workers.processor import run_pending_jobs_once

    logger.info("inline_worker_started", extra={"event": "worker.started"})

    while True:
        try:
            await run_pending_jobs_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "inline_worker_iteration_failed",
                extra={"event": "worker.iteration_failed"},
            )

        await asyncio.sleep(max(settings.worker_poll_seconds, 0.5))


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.base import Base
    import app.models.models  # noqa

    worker_task = None

    if settings.auto_create_schema:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Run seeding after migrations/schema initialization.
    await seed_defaults()

    if settings.inline_worker_enabled:
        worker_task = asyncio.create_task(
            run_inline_worker(),
            name="dps-inline-worker",
        )
        logging.getLogger(__name__).info(
            "inline_worker_enabled",
            extra={"event": "worker.inline_enabled"},
        )

    try:
        yield
    finally:
        if worker_task is not None:
            worker_task.cancel()
            await asyncio.gather(worker_task, return_exceptions=True)

        await engine.dispose()

app = FastAPI(title=settings.app_name, version="0.18.0", docs_url="/docs", redoc_url="/redoc", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["GET","POST","PATCH","PUT","DELETE","OPTIONS"], allow_headers=["Authorization","Content-Type","X-Correlation-ID"])

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    cid = correlation_id.get(None)
    logging.getLogger(__name__).warning(
        "request_validation_failed",
        extra={"event": "request.validation_failed", "path": request.url.path},
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "correlation_id": cid},
    )


@app.exception_handler(InvalidTransition)
async def invalid_transition_handler(request: Request, exc: InvalidTransition):
    return JSONResponse(status_code=409, content={"detail": str(exc), "correlation_id": correlation_id.get(None)})


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    import uuid
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    token = correlation_id.set(cid)
    started = __import__("time").perf_counter()
    path = request.url.path
    request_started.labels(request.method, path).inc()
    try:
        response = await call_next(request)
    except Exception:
        logging.getLogger(__name__).exception("request_unhandled_exception", extra={"event": "request.unhandled_exception", "path": path})
        response = JSONResponse(status_code=500, content={"detail":"Internal server error", "correlation_id": cid})
        request_failed.labels(request.method, path, "500").inc()
    finally:
        request_duration.labels(request.method, path).observe(__import__("time").perf_counter() - started)
        correlation_id.reset(token)
    if response.status_code >= 400:
        request_failed.labels(request.method, path, str(response.status_code)).inc()
    response.headers["X-Correlation-ID"] = cid
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.get("/metrics")
async def metrics():
    if not settings.metrics_enabled:
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root(): return {"name": settings.app_name, "version": "0.18.0", "docs": "/docs", "api": "/api/v1"}

for router in [health.router, meta.router, auth.router, users.router, candidates.router, interviews.router, recordings.router, processing.router, templates.router, transcripts.router, summaries.router, forms.router, reviews.router, admin.router]:
    app.include_router(router, prefix="/api/v1")
