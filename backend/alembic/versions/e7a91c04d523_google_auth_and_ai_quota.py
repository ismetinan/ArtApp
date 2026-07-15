"""users.google_sub + ai_usage günlük kota tablosu

Revision ID: e7a91c04d523
Revises: c41d2f8ab910
Create Date: 2026-07-15
"""

import sqlalchemy as sa
from alembic import op

revision = "e7a91c04d523"
down_revision = "c41d2f8ab910"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_sub", sa.String(64), nullable=True))
    op.create_unique_constraint("uq_users_google_sub", "users", ["google_sub"])
    op.create_table(
        "ai_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("day", sa.String(10), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "day"),
    )


def downgrade() -> None:
    op.drop_table("ai_usage")
    op.drop_constraint("uq_users_google_sub", "users")
    op.drop_column("users", "google_sub")
