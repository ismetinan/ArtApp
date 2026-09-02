"""Apple App Review (Guideline 2.1a) için içerik dolu demo hesap seed'i.

İki hesap üretir (varsa önce temizler, yani idempotent):

  1. Öğrenci  demo@artora.app        / ArtoraDemo2026!
     - Dolu Ability Chart, 3 ödev + AI redline analizi, biri toplulukta paylaşılmış,
       bir mentora gönderilmiş + cevaplanmış istek (mesaj/geri bildirim görünür).
     - Premium DEĞİL ve altın jetonu var: böylece Premium + jeton IAP'leri mağazada
       görünür ve sandbox'ta satın alınabilir (Guideline 2.1b).

  2. Mentor    demo.mentor@artora.app / ArtoraMentor2026!
     - Onaylı mentor profili (portfolyo + bio + stiller), gelen 1 cevaplanmış +
       1 bekleyen havuz isteğiyle mentor panelini gösterir.

Çalıştırma — prod ortam değişkenleriyle (Postgres + R2):

    railway run python -m app.scripts.seed_demo

veya prod DATABASE_URL / R2 anahtarlarını export edip:

    python -m app.scripts.seed_demo

Not: STORAGE_BACKEND=s3 iken görseller gerçek R2'ye yüklenir; kimlik bilgileri
ortamda olmalı. Görseller pakete gömülüdür (app/scripts/demo_assets), deploy
kök dizininden bağımsız çalışır.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from ..ai.mock import MockAIProvider
from ..ai.schemas import SkillAxis
from ..db import SessionLocal
from ..models.tables import (
    AbilityScore,
    JetonTransaction,
    MentorProfile,
    MentorshipRequest,
    SkillNode,
    Submission,
    User,
    UserProgress,
)
from ..services.auth import generate_token, hash_password, hash_token
from ..services.storage import delete_drawing, save_drawing

STUDENT_EMAIL = "demo@artora.app"
STUDENT_PW = "ArtoraDemo2026!"
MENTOR_EMAIL = "demo.mentor@artora.app"
MENTOR_PW = "ArtoraMentor2026!"

_ASSETS = Path(__file__).parent / "demo_assets"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_user(email: str, pw: str, name: str, level: int) -> User:
    return User(
        email=email,
        password_hash=hash_password(pw),
        api_token=hash_token(generate_token()),
        display_name=name,
        is_guest=False,
        language="tr",
        level=level,
        xp=level * 250,
    )


def _purge(db) -> None:
    """Var olan demo hesaplarını ve ürettiğimiz tüm bağlı satırları temizler
    (FK-güvenli sıra; R2 dosyaları da silinir). Yalnız bu script'in oluşturduğu
    tablolara dokunur."""
    users = db.execute(
        select(User).where(User.email.in_([STUDENT_EMAIL, MENTOR_EMAIL]))
    ).scalars().all()
    if not users:
        return
    ids = [u.id for u in users]

    # Önce R2'deki görseller
    subs = db.execute(
        select(Submission).where(Submission.user_id.in_(ids))
    ).scalars().all()
    for s in subs:
        try:
            delete_drawing(s.file_path)
        except Exception:  # noqa: BLE001 - eksik dosya seed'i durdurmasın
            pass

    db.query(JetonTransaction).filter(JetonTransaction.user_id.in_(ids)).delete(
        synchronize_session=False
    )
    db.query(MentorshipRequest).filter(
        (MentorshipRequest.student_id.in_(ids))
        | (MentorshipRequest.mentor_id.in_(ids))
    ).delete(synchronize_session=False)
    db.query(AbilityScore).filter(AbilityScore.user_id.in_(ids)).delete(
        synchronize_session=False
    )
    db.query(UserProgress).filter(UserProgress.user_id.in_(ids)).delete(
        synchronize_session=False
    )
    db.query(MentorProfile).filter(MentorProfile.user_id.in_(ids)).delete(
        synchronize_session=False
    )
    db.query(Submission).filter(Submission.user_id.in_(ids)).delete(
        synchronize_session=False
    )
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.flush()


def _asset(name: str) -> bytes:
    return (_ASSETS / name).read_bytes()


def _add_submission(
    db, user: User, provider: MockAIProvider, asset: str, node_id: str | None,
    lesson: str, public: bool,
) -> Submission:
    content = _asset(asset)
    rel_path = save_drawing(content, asset)
    result = asyncio.run(provider.redline_analysis(content, lesson, "tr"))
    sub = Submission(
        user_id=user.id,
        node_id=node_id,
        kind="assignment",
        file_path=rel_path,
        ai_result=result.model_dump(mode="json"),
        is_public=public,
        moderation_status="safe" if public else "unchecked",
    )
    db.add(sub)
    db.flush()
    return sub


def seed() -> None:
    provider = MockAIProvider()
    with SessionLocal() as db:
        _purge(db)

        # Gerçek düğümlere bağla (varsa) — yoksa node_id boş kalır
        node_ids = db.execute(select(SkillNode.id).limit(3)).scalars().all()
        n = lambda i: node_ids[i] if i < len(node_ids) else None  # noqa: E731

        # --- Öğrenci ---
        student = _new_user(STUDENT_EMAIL, STUDENT_PW, "Demo Çizer", level=5)
        # Premium DEĞİL. 5 altın (paid) + 3 ücretsiz = 8 jeton; altın seçmeli mentoru
        # test etmeye yeter, IAP'ler yine mağazada görünür.
        student.jeton_balance = 8
        student.jeton_paid_balance = 5
        db.add(student)
        db.flush()

        # Ability Chart (7 eksen)
        demo_scores = {
            SkillAxis.ANATOMI: 62,
            SkillAxis.PERSPEKTIF: 48,
            SkillAxis.ISIK_GOLGE: 55,
            SkillAxis.ORAN: 70,
            SkillAxis.CIZGI_KALITESI: 74,
            SkillAxis.KOMPOZISYON: 51,
            SkillAxis.RENK: 40,
        }
        for axis, score in demo_scores.items():
            db.add(AbilityScore(user_id=student.id, axis=axis.value, score=score))

        # Ödevler + AI analizi
        s1 = _add_submission(
            db, student, provider, "drawing1.jpg", n(0), "Çizgi Temelleri", public=True
        )
        _add_submission(
            db, student, provider, "drawing2.jpg", n(1), "Şekil ve Form", public=False
        )
        _add_submission(
            db, student, provider, "drawing3.jpg", n(2), "Perspektif", public=False
        )

        # Tamamlanmış ders + jeton geçmişi
        if n(0):
            db.add(UserProgress(user_id=student.id, node_id=n(0), xp_earned=40))
        db.add(JetonTransaction(user_id=student.id, delta=3, reason="welcome"))

        # --- Mentor ---
        mentor = _new_user(MENTOR_EMAIL, MENTOR_PW, "Demo Mentor", level=6)
        mentor.jeton_balance = 3
        db.add(mentor)
        db.flush()

        mentor_sub = _add_submission(
            db, mentor, provider, "drawing2.jpg", n(0), "Portre", public=True
        )
        db.add(MentorProfile(
            user_id=mentor.id,
            bio="10 yıllık portre ve figür çizeriyim; anatomi ve ışık-gölge üzerine "
                "yapıcı geri bildirim veriyorum.",
            styles=["realist", "portre"],
            portfolio_submission_ids=[mentor_sub.id],
            status="approved",
            is_available=True,
            sample_critique="Figürün omuz hattı gövdenin dönüşüyle uyumlu, çizgi güvenin "
                "belirgin. Bir sonraki adımda ışık kaynağını tek yönde sabitleyip "
                "gölgeleri ona göre kur — form hemen oturacak.",
            rules_accepted_at=_now(),
        ))
        db.flush()

        # Cevaplanmış havuz isteği (öğrenci → mentor): mesaj/geri bildirim görünür
        db.add(MentorshipRequest(
            submission_id=s1.id,
            student_id=student.id,
            mentor_id=mentor.id,
            jeton_cost=1,
            status="answered",
            feedback_text="Kompozisyon dengeli ve çizgilerin akıcı. Baş-gövde oranını "
                "7-8 baş ölçüsüyle kontrol edersen figür daha inandırıcı olur. Işık "
                "kaynağını netleştirmen gölgeleri de toparlayacak — güzel iş, devam et!",
            rating=5,
            assigned_at=_now() - timedelta(days=1),
            answered_at=_now() - timedelta(hours=20),
        ))
        db.add(JetonTransaction(
            user_id=student.id, delta=-1, reason="mentor_request"
        ))

        db.commit()

    print("Demo hesaplar hazır:")
    print(f"  Öğrenci : {STUDENT_EMAIL} / {STUDENT_PW}")
    print(f"  Mentor  : {MENTOR_EMAIL} / {MENTOR_PW}")


if __name__ == "__main__":
    seed()
