"""Ödevin yapılandırılmış hâli (2026-10): assignments.brief (JSON, nullable).

Eski ödevlerde NULL kalır; istemci metne düşer. Backfill yok — öğrenci yarıda
olabilir, mevcut ödev metni değişmemeli.

Revision ID: d6a2b8f1e4c3
Revises: c5f9a3e7b2d4
Create Date: 2026-10-11
"""

import sqlalchemy as sa
from alembic import op

revision = "d6a2b8f1e4c3"
down_revision = "c5f9a3e7b2d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assignments", sa.Column("brief", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("assignments", "brief")
