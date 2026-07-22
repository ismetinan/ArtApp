"""Faz 4 (gelir paylaşımı) Faz A: mentor_earnings kazanç defteri.

Tabloyu oluşturur ve mevcut TÜM answered mentorship_request'ler için geriye dönük
kazanç satırı işler — erken mentorlar beta boyunca verdikleri emeği kaybetmesin.

Revision ID: c3d9f1a2b8e4
Revises: d2f8c46b9e17
Create Date: 2026-07-22
"""

import sqlalchemy as sa
from alembic import op

revision = "c3d9f1a2b8e4"
down_revision = "d2f8c46b9e17"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mentor_earnings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mentor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "request_id",
            sa.Integer(),
            sa.ForeignKey("mentorship_requests.id"),
            nullable=True,
            unique=True,
        ),
        sa.Column("jeton_equivalent", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=24), nullable=False, server_default="mentor_feedback"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mentor_earnings_mentor_id", "mentor_earnings", ["mentor_id"])

    # Geriye dönük backfill: cevaplanmış istekleri mentor kazancına yaz.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO mentor_earnings
                (mentor_id, request_id, jeton_equivalent, reason, created_at)
            SELECT mentor_id, id, jeton_cost, 'mentor_feedback',
                   COALESCE(answered_at, created_at)
            FROM mentorship_requests
            WHERE status = 'answered' AND mentor_id IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_mentor_earnings_mentor_id", table_name="mentor_earnings")
    op.drop_table("mentor_earnings")
