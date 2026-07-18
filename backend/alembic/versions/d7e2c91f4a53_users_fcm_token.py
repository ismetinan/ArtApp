"""users.fcm_token — FCM push bildirimleri için cihaz token'ı

Revision ID: d7e2c91f4a53
Revises: a9c4e58b1f02
Create Date: 2026-07-18
"""

import sqlalchemy as sa
from alembic import op

revision = "d7e2c91f4a53"
down_revision = "a9c4e58b1f02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("fcm_token", sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "fcm_token")
