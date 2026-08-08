"""Bağış linki + mentor kalite kapısı (jeton = AI ekonomisi, 2026-08-08).

Hepsi additive, veri göçü YOK — mevcut mentor profillerinde:
- sample_critique "" kalır (eski onaylı mentorlar geriye dönük kritik yazmaz),
- rules_accepted_at / rejected_at / donation_url NULL kalır,
- donation_status "pending" olur ama donation_url NULL olduğu için hiçbir yerde
  bağış kartı görünmez (bkz. mentors.py _profile_json: url VE approved şartı).

Revision ID: b4e17c9a3d20
Revises: f7a2d3c9b1e6
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op

revision = "b4e17c9a3d20"
down_revision = "f7a2d3c9b1e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mentor_profiles",
        sa.Column("sample_critique", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "mentor_profiles",
        sa.Column("rules_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "mentor_profiles",
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "mentor_profiles", sa.Column("donation_url", sa.String(length=300), nullable=True)
    )
    op.add_column(
        "mentor_profiles",
        sa.Column("donation_platform", sa.String(length=24), nullable=True),
    )
    op.add_column(
        "mentor_profiles",
        sa.Column(
            "donation_status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
        ),
    )


def downgrade() -> None:
    op.drop_column("mentor_profiles", "donation_status")
    op.drop_column("mentor_profiles", "donation_platform")
    op.drop_column("mentor_profiles", "donation_url")
    op.drop_column("mentor_profiles", "rejected_at")
    op.drop_column("mentor_profiles", "rules_accepted_at")
    op.drop_column("mentor_profiles", "sample_critique")
