"""Önleyici içerik filtresi: submissions.moderation_status

Revision ID: a7f3e85d21c9
Revises: e5d9b31c7a86
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op

revision = "a7f3e85d21c9"
down_revision = "e5d9b31c7a86"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column(
            "moderation_status",
            sa.String(12),
            nullable=False,
            server_default="unchecked",
        ),
    )


def downgrade() -> None:
    op.drop_column("submissions", "moderation_status")
