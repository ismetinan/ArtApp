"""Analitik (2026-09): aktif günler, istemci olayları, son görülme/platform.

Yeni tablolar: user_activity_days, app_events. users'a üç nullable kolon.

Geriye dönük doldurma: aktiflik tablosu bugünden itibaren dolacağı için, geçmiş
retention'ı hemen görebilmek adına mevcut zaman damgalı kayıtlardan (kayıt,
gönderi, jeton hareketi, ders tamamlama, analiz işi) aktif günler türetilir.
Yalnız Postgres'te — testler create_all kullanıyor.

Revision ID: a1d5e0c7f3b2
Revises: c92f4b18de37
Create Date: 2026-09-26
"""

import sqlalchemy as sa
from alembic import op

revision = "a1d5e0c7f3b2"
down_revision = "c92f4b18de37"
branch_labels = None
depends_on = None

_BACKFILL_SOURCES = (
    ("users", "id", "created_at"),
    ("submissions", "user_id", "created_at"),
    ("jeton_transactions", "user_id", "created_at"),
    ("user_progress", "user_id", "completed_at"),
    ("analysis_jobs", "user_id", "created_at"),
)


def upgrade() -> None:
    op.add_column("users", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("platform", sa.String(16), nullable=True))
    op.add_column("users", sa.Column("app_version", sa.String(32), nullable=True))

    op.create_table(
        "user_activity_days",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.UniqueConstraint("user_id", "day"),
    )
    op.create_index("ix_user_activity_days_user_id", "user_activity_days", ["user_id"])
    op.create_index("ix_user_activity_days_day", "user_activity_days", ["day"])

    op.create_table(
        "app_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("props", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_app_events_user_id", "app_events", ["user_id"])
    op.create_index("ix_app_events_name", "app_events", ["name"])
    op.create_index("ix_app_events_created_at", "app_events", ["created_at"])

    if op.get_bind().dialect.name == "postgresql":
        union = " UNION ".join(
            f"SELECT {uid} AS user_id, ({ts} AT TIME ZONE 'UTC')::date AS day "
            f"FROM {table} WHERE {ts} IS NOT NULL"
            for table, uid, ts in _BACKFILL_SOURCES
        )
        op.execute(
            "INSERT INTO user_activity_days (user_id, day) "
            f"SELECT DISTINCT user_id, day FROM ({union}) AS src "
            "ON CONFLICT (user_id, day) DO NOTHING"
        )
        # Son görülme yaklaşığı: en son aktif gün
        op.execute(
            "UPDATE users SET last_seen_at = sub.last_day "
            "FROM (SELECT user_id, (MAX(day)::timestamp AT TIME ZONE 'UTC') AS last_day "
            "FROM user_activity_days GROUP BY user_id) AS sub "
            "WHERE users.id = sub.user_id"
        )


def downgrade() -> None:
    op.drop_table("app_events")
    op.drop_table("user_activity_days")
    op.drop_column("users", "app_version")
    op.drop_column("users", "platform")
    op.drop_column("users", "last_seen_at")
