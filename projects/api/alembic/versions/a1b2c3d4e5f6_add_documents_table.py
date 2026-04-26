"""add documents table

Revision ID: a1b2c3d4e5f6
Revises: 4fd50ef2630a
Create Date: 2026-04-26 08:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4fd50ef2630a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "documents",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column(
            "embedding_status",
            sa.String(),
            server_default="pending",
            nullable=False,
        ),
        sa.CheckConstraint("file_size >= 0", name="ck_documents_file_size_nonneg"),
        sa.UniqueConstraint("storage_path", name="uq_documents_storage_path"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_documents_content_hash", "documents", ["content_hash"], unique=False
    )
    op.create_index(
        "ix_documents_embedding_status",
        "documents",
        ["embedding_status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_documents_embedding_status", table_name="documents")
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_table("documents")
