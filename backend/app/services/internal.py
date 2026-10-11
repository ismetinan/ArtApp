"""Dahili (demo / App Review) hesaplar (2026-10).

Demo hesaplar (scripts/seed_demo.py) Apple incelemesi için prod'da duruyor ama
gerçek kullanıcılara görünmemeli: topluluk galerisinde demo çizimler, mentor
listesinde demo mentorlar çıkıyordu; daha kötüsü havuz eşleştirmesi gerçek bir
öğrencinin isteğini hiç cevap vermeyecek demo mentora atayabiliyordu.

Kural: dahili içerik yalnız dahili hesaplara görünür. Reviewer demo hesapla
girdiğinde her şeyi dolu görmeye devam eder.
"""

from sqlalchemy import or_

from ..models.tables import User

INTERNAL_EMAIL_SUFFIX = "@artora.app"


def is_internal(user: User | None) -> bool:
    return bool(user and user.email and user.email.lower().endswith(INTERNAL_EMAIL_SUFFIX))


def not_internal_clause():
    """SQL: dahili OLMAYAN kullanıcılar (User tablosu sorguya katılmış olmalı)."""
    return or_(User.email.is_(None), ~User.email.like(f"%{INTERNAL_EMAIL_SUFFIX}"))


def visibility_clause(viewer: User):
    """Bakan kişiye göre görünür kullanıcılar: dahili bakan herkesi görür,
    gerçek kullanıcı dahilileri görmez. None = filtre yok."""
    return None if is_internal(viewer) else not_internal_clause()
