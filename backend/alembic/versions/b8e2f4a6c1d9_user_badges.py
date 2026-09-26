"""Rozetler (2026-09): user_badges tablosu.

Katalog kodda (services/badges.py); burada yalnız kazanılmış rozetler.
Mevcut kullanıcılar ilerleme rozetlerini ilk /profile açılışında tembel
olarak alır — backfill gerekmez.

Revision ID: b8e2f4a6c1d9
Revises: a1d5e0c7f3b2
Create Date: 2026-09-26
"""

import sqlalchemy as sa
from alembic import op

revision = "b8e2f4a6c1d9"
down_revision = "a1d5e0c7f3b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_badges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "code"),
    )
    op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_badges")
