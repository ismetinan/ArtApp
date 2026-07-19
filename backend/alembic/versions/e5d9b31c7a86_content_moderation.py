"""UGC moderasyonu: content_reports + submissions.moderation_hidden

Revision ID: e5d9b31c7a86
Revises: c8f4a72e91d5
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op

revision = "e5d9b31c7a86"
down_revision = "c8f4a72e91d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column(
            "moderation_hidden", sa.Boolean, nullable=False, server_default=sa.false()
        ),
    )
    op.create_table(
        "content_reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "submission_id", sa.Integer, sa.ForeignKey("submissions.id"), nullable=False
        ),
        sa.Column("reporter_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", "reporter_id"),
    )


def downgrade() -> None:
    op.drop_table("content_reports")
    op.drop_column("submissions", "moderation_hidden")
