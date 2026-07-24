"""Faz 4: haftalık ücretsiz jeton damlası için son-damla zaman damgası.

Tek additive kolon: users.free_jeton_last_grant (nullable). Mevcut kullanıcılarda
NULL kalır — ilk /profile açılışında bir kez damlar, sonra 7 günde bir. Bakiye
göçü YOK (altın = mevcut jeton_paid_balance olarak aynen kullanılır).

Revision ID: f7a2d3c9b1e6
Revises: e5b1c7a04f92
Create Date: 2026-07-24
"""

import sqlalchemy as sa
from alembic import op

revision = "f7a2d3c9b1e6"
down_revision = "e5b1c7a04f92"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("free_jeton_last_grant", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "free_jeton_last_grant")
