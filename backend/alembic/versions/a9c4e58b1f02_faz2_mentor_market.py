"""Faz 2 mentor pazarı: mentor_profiles, mentorship_requests, jeton_transactions,
users.is_admin + mevcut kullanıcılara 3 hoşgeldin jetonu backfill'i

Revision ID: a9c4e58b1f02
Revises: f3b8a217d641
Create Date: 2026-07-18
"""

import sqlalchemy as sa
from alembic import op

revision = "a9c4e58b1f02"
down_revision = "f3b8a217d641"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "mentor_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("bio", sa.Text(), nullable=False, server_default=""),
        sa.Column("styles", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("portfolio_submission_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "mentorship_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("mentor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("jeton_cost", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(16), nullable=False, server_default="assigned"),
        sa.Column("feedback_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "jeton_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(24), nullable=False),
        sa.Column(
            "request_id", sa.Integer(), sa.ForeignKey("mentorship_requests.id"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Backfill: mevcut kullanıcılara 3 hoşgeldin jetonu (transaction kaydıyla).
    # Yalnız hiç jetonu olmayanlara — migration tekrar koşarsa çift vermesin.
    op.execute(
        "INSERT INTO jeton_transactions (user_id, delta, reason, created_at) "
        "SELECT id, 3, 'welcome', now() FROM users WHERE jeton_balance = 0"
    )
    op.execute("UPDATE users SET jeton_balance = 3 WHERE jeton_balance = 0")


def downgrade() -> None:
    op.drop_table("jeton_transactions")
    op.drop_table("mentorship_requests")
    op.drop_table("mentor_profiles")
    op.drop_column("users", "is_admin")
