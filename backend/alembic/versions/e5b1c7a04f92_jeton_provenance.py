"""Faz 4 (gelir paylaşımı): jeton kaynağı (ücretsiz/gelir-destekli) takibi.

Üç kolon ekler:
- users.jeton_paid_balance: bakiyenin gelir-destekli (satın alma/Premium) kısmı
- mentorship_requests.paid_cost: harcamanın gelir-destekli parçası (önce-ücretsiz)
- mentor_earnings.paid_equivalent: kazancın nakde çevrilebilir kısmı

Mevcut satırlar için hepsi 0 (server_default) — geçmiş bakiyelerin kaynağı
bilinmediğinden temkinli olarak ÜCRETSİZ sayılır (nakit yükümlülüğü doğurmaz).
Provenans takibi bu migration'dan itibaren doğru işler.

Revision ID: e5b1c7a04f92
Revises: c3d9f1a2b8e4
Create Date: 2026-07-22
"""

import sqlalchemy as sa
from alembic import op

revision = "e5b1c7a04f92"
down_revision = "c3d9f1a2b8e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("jeton_paid_balance", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "mentorship_requests",
        sa.Column("paid_cost", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "mentor_earnings",
        sa.Column("paid_equivalent", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("mentor_earnings", "paid_equivalent")
    op.drop_column("mentorship_requests", "paid_cost")
    op.drop_column("users", "jeton_paid_balance")
