"""Topluluk beğenileri (2026-10): submission_likes.

Revision ID: e8c4d1a9b7f5
Revises: d6a2b8f1e4c3
Create Date: 2026-10-11
"""

import sqlalchemy as sa
from alembic import op

revision = "e8c4d1a9b7f5"
down_revision = "d6a2b8f1e4c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "submission_likes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", "user_id"),
    )
    op.create_index("ix_submission_likes_submission_id", "submission_likes", ["submission_id"])
    op.create_index("ix_submission_likes_user_id", "submission_likes", ["user_id"])


def downgrade() -> None:
    op.drop_table("submission_likes")
