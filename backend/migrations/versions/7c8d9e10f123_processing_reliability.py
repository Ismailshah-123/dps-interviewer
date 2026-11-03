"""processing reliability fields

Revision ID: 7c8d9e10f123
Revises: 42ab447c5d18
"""
from alembic import op
import sqlalchemy as sa

revision = "7c8d9e10f123"
down_revision = "42ab447c5d18"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("processing_jobs", sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("processing_jobs", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    op.create_index("ix_processing_jobs_idempotency_key", "processing_jobs", ["idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_processing_jobs_idempotency_key", table_name="processing_jobs")
    op.drop_column("processing_jobs", "idempotency_key")
    op.drop_column("processing_jobs", "max_attempts")
