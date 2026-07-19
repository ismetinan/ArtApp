"""Güvenlik: users.api_token artık SHA-256 hash olarak saklanır.

Mevcut ham token'lar yerinde hash'lenir — canlı istemciler oturum kaybetmez:
istemcinin gönderdiği ham token, girişte hash'lenip aynı satırı bulur.
(Ham ve hash aynı 64 karakterlik hex biçiminde; bu migration alembic
tarafından tek kez koşulur, tekrar hash'leme riski yok.)

Revision ID: d2f8c46b9e17
Revises: a7f3e85d21c9
Create Date: 2026-07-19
"""

import hashlib

import sqlalchemy as sa
from alembic import op

revision = "d2f8c46b9e17"
down_revision = "a7f3e85d21c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, api_token FROM users")).fetchall()
    for user_id, token in rows:
        if not token:
            continue
        conn.execute(
            sa.text("UPDATE users SET api_token = :h WHERE id = :i"),
            {"h": hashlib.sha256(token.encode()).hexdigest(), "i": user_id},
        )


def downgrade() -> None:
    # Hash geri çevrilemez — downgrade tüm oturumları düşürmek anlamına gelirdi;
    # bilinçli olarak no-op bırakıldı (kullanıcılar yeniden giriş yapar).
    pass
