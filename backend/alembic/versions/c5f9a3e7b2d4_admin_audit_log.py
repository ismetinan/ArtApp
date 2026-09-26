"""Admin denetim kaydı (güvenlik, 2026-09).

Revision ID: c5f9a3e7b2d4
Revises: b8e2f4a6c1d9
Create Date: 2026-09-26
"""

import sqlalchemy as sa
from alembic import op

revision = "c5f9a3e7b2d4"
down_revision = "b8e2f4a6c1d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("target_type", sa.String(24), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_admin_audit_logs_created_at", "admin_audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("admin_audit_logs")
