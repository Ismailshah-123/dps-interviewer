from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings
from app.services.transcription.factory import get_transcription_provider
from app.services.summarization.factory import get_summarization_provider

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/live")
async def live():
    return {"status": "alive"}

@router.get("/ready")
async def ready():
    checks = {"database": "ok", "storage": "ok", "transcription_provider": settings.transcription_provider, "summarization_provider": settings.summarization_provider}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "unavailable"
    try:
        from pathlib import Path
        Path(settings.storage_root).mkdir(parents=True, exist_ok=True)
        probe = Path(settings.storage_root) / ".healthcheck"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except Exception:
        checks["storage"] = "unavailable"
    if checks["database"] != "ok" or checks["storage"] != "ok":
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}


@router.get("/ai")
async def ai_health():
    """Return non-invasive AI configuration health without making billable/quota-consuming calls."""
    checks = {}
    for name, factory in (("transcription", get_transcription_provider), ("summarization", get_summarization_provider)):
        try:
            provider = factory()
            checks[name] = {"status": "configured", "provider": provider.name, "model": provider.model_name}
        except Exception as exc:
            checks[name] = {"status": "unavailable", "error": type(exc).__name__}
    ready = all(item["status"] == "configured" for item in checks.values())
    payload = {"status": "ready" if ready else "degraded", "checks": checks}
    if not ready:
        raise HTTPException(status_code=503, detail=payload)
    return payload
