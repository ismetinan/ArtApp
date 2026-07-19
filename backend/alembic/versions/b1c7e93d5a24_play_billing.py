"""Play Billing: purchases tablosu + users.premium_until

Revision ID: b1c7e93d5a24
Revises: d7e2c91f4a53
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op

revision = "b1c7e93d5a24"
down_revision = "d7e2c91f4a53"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("premium_until", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", sa.String(64), nullable=False),
        sa.Column("purchase_token", sa.String(512), nullable=False, unique=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("granted_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("purchases")
    op.drop_column("users", "premium_until")
