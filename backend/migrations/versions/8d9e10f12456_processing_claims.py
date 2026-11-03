"""durable processing claims and retry scheduling

Revision ID: 8d9e10f12456
Revises: 7c8d9e10f123
"""
from alembic import op
import sqlalchemy as sa

revision = "8d9e10f12456"
down_revision = "7c8d9e10f123"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("processing_jobs", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("processing_jobs", sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("processing_jobs", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_processing_jobs_next_attempt_at", "processing_jobs", ["next_attempt_at"])
    op.create_index("ix_processing_jobs_locked_at", "processing_jobs", ["locked_at"])
    op.create_index("ix_processing_job_due", "processing_jobs", ["status", "next_attempt_at", "created_at"])

def downgrade() -> None:
    op.drop_index("ix_processing_job_due", table_name="processing_jobs")
    op.drop_index("ix_processing_jobs_locked_at", table_name="processing_jobs")
    op.drop_index("ix_processing_jobs_next_attempt_at", table_name="processing_jobs")
    op.drop_column("processing_jobs", "heartbeat_at")
    op.drop_column("processing_jobs", "locked_at")
    op.drop_column("processing_jobs", "next_attempt_at")
