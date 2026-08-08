"""Asenkron AI analiz işleri (Faz 2, 2026-08-08).

Tek yeni tablo; mevcut veriye dokunulmuyor. Senkron uçlar yerinde kalmaya
devam ediyor (eski istemciler kırılmasın), yeni -async uçları bu tabloyu
kullanıyor.

Revision ID: c92f4b18de37
Revises: b4e17c9a3d20
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op

revision = "c92f4b18de37"
down_revision = "b4e17c9a3d20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column(
            "node_id", sa.String(length=64), sa.ForeignKey("skill_nodes.id"), nullable=True
        ),
        sa.Column(
            "submission_id", sa.Integer(), sa.ForeignKey("submissions.id"), nullable=True
        ),
        sa.Column(
            "status", sa.String(length=16), nullable=False, server_default="queued"
        ),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.Column("xp_awarded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jeton_cost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "refunded", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Kurtarma sorgusu: kullanıcının son işi + takılı kalanların taranması
    op.create_index("ix_analysis_jobs_user_id", "analysis_jobs", ["user_id"])
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status"])

    # Faz 3: eksen skorunun zaman serisi
    op.create_table(
        "ability_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("axis", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("ix_ability_history_user_id", "ability_history", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_ability_history_user_id", table_name="ability_history")
    op.drop_table("ability_history")
    op.drop_index("ix_analysis_jobs_status", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_user_id", table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
