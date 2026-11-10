"""stored PDF documents and review transition metadata

Revision ID: b7c8d9e10f12
Revises: 8d9e10f12456
"""
from alembic import op
import sqlalchemy as sa

revision = "b7c8d9e10f12"
down_revision = "8d9e10f12456"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stored_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("interview_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=40), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
        sa.UniqueConstraint("interview_id", "document_type", "version_number", name="uq_stored_document_interview_version"),
    )
    op.create_index("ix_stored_documents_interview_id", "stored_documents", ["interview_id"])
    op.create_index("ix_stored_documents_sha256", "stored_documents", ["sha256"])
    op.add_column("interview_reviews", sa.Column("status_from", sa.String(length=40), nullable=True))
    op.add_column("interview_reviews", sa.Column("status_to", sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column("interview_reviews", "status_to")
    op.drop_column("interview_reviews", "status_from")
    op.drop_index("ix_stored_documents_sha256", table_name="stored_documents")
    op.drop_index("ix_stored_documents_interview_id", table_name="stored_documents")
    op.drop_table("stored_documents")
