"""AI ödev üretimi (assignments) + pazara çıkış bekleme listesi (waitlist_signups)

Revision ID: c8f4a72e91d5
Revises: b1c7e93d5a24
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op

revision = "c8f4a72e91d5"
down_revision = "b1c7e93d5a24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("node_id", sa.String(64), sa.ForeignKey("skill_nodes.id"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "node_id"),
    )
    op.create_table(
        "waitlist_signups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("waitlist_signups")
    op.drop_table("assignments")
