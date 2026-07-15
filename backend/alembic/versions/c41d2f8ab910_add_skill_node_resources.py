"""add skill_nodes.resources (müfredat video/playlist listesi)

Revision ID: c41d2f8ab910
Revises: 8053f92ed670
Create Date: 2026-07-15
"""

import sqlalchemy as sa
from alembic import op

revision = "c41d2f8ab910"
down_revision = "8053f92ed670"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "skill_nodes",
        sa.Column("resources", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("skill_nodes", "resources")
