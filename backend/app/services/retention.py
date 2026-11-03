from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.models import Interview, Recording
from app.services.storage.local import LocalPrivateStorage

async def purge_old_recordings(dry_run: bool = True) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_days)
    storage = LocalPrivateStorage()
    deleted = 0
    missing = 0
    async with SessionLocal() as db:
        rows = (await db.scalars(select(Recording).where(Recording.created_at < cutoff))).all()
        for recording in rows:
            path = storage.path_for(recording.storage_key)
            if not path.exists():
                missing += 1
            if not dry_run:
                storage.delete(recording.storage_key)
                await db.delete(recording)
                deleted += 1
        if not dry_run:
            await db.commit()
    return {"cutoff": cutoff.isoformat(), "candidates": len(rows), "deleted": deleted, "missing": missing, "dry_run": dry_run}
