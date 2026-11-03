from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditEvent
from app.core.request_context import correlation_id as request_correlation_id

async def record_audit(db: AsyncSession, *, actor_user_id: UUID | None, action: str, resource_type: str, resource_id: str | UUID | None = None, correlation_id: str | None = None, metadata: dict | None = None, commit: bool = False):
    event = AuditEvent(actor_user_id=actor_user_id, action=action, resource_type=resource_type, resource_id=str(resource_id) if resource_id else None, correlation_id=correlation_id or request_correlation_id.get(), metadata_json=metadata or {})
    db.add(event)
    if commit:
        await db.commit()
    return event
