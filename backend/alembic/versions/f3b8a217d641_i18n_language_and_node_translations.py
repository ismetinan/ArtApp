"""i18n: users.language + skill_nodes EN çevirileri

Revision ID: f3b8a217d641
Revises: e7a91c04d523
Create Date: 2026-07-18
"""

import sqlalchemy as sa
from alembic import op

revision = "f3b8a217d641"
down_revision = "e7a91c04d523"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("language", sa.String(5), nullable=False, server_default="tr"),
    )
    op.add_column(
        "skill_nodes",
        sa.Column("title_en", sa.String(200), nullable=False, server_default=""),
    )
    op.add_column(
        "skill_nodes",
        sa.Column("description_en", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("skill_nodes", "description_en")
    op.drop_column("skill_nodes", "title_en")
    op.drop_column("users", "language")
