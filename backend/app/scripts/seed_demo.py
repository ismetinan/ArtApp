"""Apple App Review (Guideline 2.1a) için içerik dolu demo hesap seed'i.

TEK giriş = tüm özellikler. Reviewer bir hesapla her şeyi görebilsin diye ana
demo hesabı hem ONAYLI MENTOR hem de geri bildirim ALMIŞ bir öğrencidir.

  ANA HESAP  demo@artora.app / ArtoraDemo2026!
    - Seviye 5 (topluluk paylaşımı 3+ gerektirir → kilit açık).
    - Onaylı mentor profili: bio, stiller, portfolyo (kendi galerisinden).
    - 3 derse ödev yüklemiş + her birine AI redline analizi almış.
    - Bir ödevini TOPLULUĞA paylaşmış (public + moderasyon geçmiş).
    - Bir mentordan geri bildirim ALMIŞ (cevaplanmış istek → mesaj görünür).
    - Mentor panelinde CEVAP BEKLEYEN bir gelen istek (mentor tarafını gösterir).
    - Premium DEĞİL + altın jetonlu → tüm IAP'ler (jeton paketleri + Premium)
      mağazada görünür ve sandbox'ta satın alınabilir (Guideline 2.1b).

  YARDIMCI  demo.helper@artora.app / ArtoraHelper2026!
    - Ana hesabın aldığı geri bildirimi VEREN onaylı mentor; ayrıca ana hesaba
      cevaplanacak bir istek gönderir (mentor paneli boş kalmasın).

Çalıştırma — prod env değişkenleriyle (Postgres + R2). Railway tüm env'i
enjekte eder, hiçbir sır transkripte düşmez:

    railway run python -m app.scripts.seed_demo

railway CLI yoksa: `npm i -g @railway/cli && railway login && railway link`,
sonra yukarıdaki komut. Görseller pakete gömülüdür (app/scripts/demo_assets),
deploy kök dizininden bağımsız çalışır. Script idempotent'tir (önce temizler).
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
    AbilityHistory,
    AbilityScore,
    AnalysisJob,
    AppEvent,
    Assignment,
    JetonTransaction,
    MentorProfile,
    MentorshipRequest,
    SkillNode,
    Submission,
    User,
    UserActivityDay,
    UserBadge,
    UserProgress,
)
from ..services.auth import generate_token, hash_password, hash_token
from ..services.storage import delete_drawing, save_drawing

MAIN_EMAIL = "demo@artora.app"
MAIN_PW = "ArtoraDemo2026!"
HELPER_EMAIL = "demo.helper@artora.app"
HELPER_PW = "ArtoraHelper2026!"

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
    tablolara dokunur → tekrar tekrar çalıştırılabilir."""
    users = db.execute(
        select(User).where(User.email.in_([MAIN_EMAIL, HELPER_EMAIL]))
    ).scalars().all()
    if not users:
        return
    ids = [u.id for u in users]

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
    # Reviewer oturumlarının ürettiği satırlar (aktiflik, olay, analiz işi…)
    for table in (
        AnalysisJob, Assignment, AbilityHistory, UserActivityDay, AppEvent, UserBadge
    ):
        db.query(table).filter(table.user_id.in_(ids)).delete(synchronize_session=False)
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

        node_ids = db.execute(select(SkillNode.id).limit(3)).scalars().all()
        n = lambda i: node_ids[i] if i < len(node_ids) else None  # noqa: E731

        # ---------------------------------------------------------------- ANA
        main = _new_user(MAIN_EMAIL, MAIN_PW, "Demo Çizer", level=5)
        # Premium DEĞİL; 5 altın (paid) + 3 ücretsiz = 8 jeton. Altın seçmeli
        # mentoru test etmeye yeter, IAP'ler yine mağazada görünür.
        main.jeton_balance = 8
        main.jeton_paid_balance = 5
        db.add(main)
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
            db.add(AbilityScore(user_id=main.id, axis=axis.value, score=score))

        # 3 ödev + AI redline; ilki topluluğa paylaşılmış
        shared = _add_submission(
            db, main, provider, "drawing1.jpg", n(0), "Çizgi Temelleri", public=True
        )
        _add_submission(
            db, main, provider, "drawing2.jpg", n(1), "Şekil ve Form", public=False
        )
        portfolio_sub = _add_submission(
            db, main, provider, "drawing3.jpg", n(2), "Portre", public=True
        )

        if n(0):
            db.add(UserProgress(user_id=main.id, node_id=n(0), xp_earned=40))
        db.add(JetonTransaction(user_id=main.id, delta=3, reason="welcome"))

        # Ana hesap ONAYLI MENTOR — portfolyo kendi galerisinden
        db.add(MentorProfile(
            user_id=main.id,
            bio="Portre ve figür üzerine çalışan bir çizerim; anatomi ve ışık-gölge "
                "konularında yapıcı, uygulanabilir geri bildirim veriyorum.",
            styles=["realist", "portre"],
            portfolio_submission_ids=[portfolio_sub.id],
            status="approved",
            is_available=True,
            sample_critique="Figürün silueti dengeli ve çizgi güvenin belirgin. Bir "
                "sonraki adımda ışık kaynağını tek yönde sabitleyip gölgeleri ona göre "
                "kurarsan form çok daha inandırıcı oturacak.",
            rules_accepted_at=_now(),
        ))

        # ------------------------------------------------------------- YARDIMCI
        helper = _new_user(HELPER_EMAIL, HELPER_PW, "Demo Mentor", level=4)
        helper.jeton_balance = 3
        db.add(helper)
        db.flush()

        helper_sub = _add_submission(
            db, helper, provider, "drawing2.jpg", n(0), "Çizgi Temelleri", public=False
        )
        db.add(MentorProfile(
            user_id=helper.id,
            bio="Manga ve karakter tasarımı odaklı mentor.",
            styles=["manga", "karakter"],
            portfolio_submission_ids=[],
            status="approved",
            is_available=True,
            sample_critique="Kompozisyon akıcı; perspektif çizgilerini biraz daha "
                "netleştirirsen derinlik hissi güçlenir.",
            rules_accepted_at=_now(),
        ))
        db.flush()

        # (1) Ana hesap geri bildirim ALDI: helper, main'in ödevini cevapladı.
        #     Öğrenci tarafında mesaj/geri bildirim görünür.
        db.add(MentorshipRequest(
            submission_id=shared.id,
            student_id=main.id,
            mentor_id=helper.id,
            jeton_cost=1,
            status="answered",
            feedback_text="Kompozisyon dengeli ve çizgilerin akıcı. Baş-gövde oranını "
                "7-8 baş ölçüsüyle kontrol edersen figür daha inandırıcı olur. Işık "
                "kaynağını netleştirmen gölgeleri de toparlayacak — güzel iş, devam et!",
            rating=5,
            assigned_at=_now() - timedelta(days=1),
            answered_at=_now() - timedelta(hours=20),
        ))
        db.add(JetonTransaction(user_id=main.id, delta=-1, reason="mentor_request"))

        # (2) Ana hesabın MENTOR PANELİ boş kalmasın: helper, main'e cevap
        #     bekleyen bir istek gönderdi.
        db.add(MentorshipRequest(
            submission_id=helper_sub.id,
            student_id=helper.id,
            mentor_id=main.id,
            jeton_cost=1,
            status="assigned",
            assigned_at=_now() - timedelta(hours=3),
        ))
        db.add(JetonTransaction(user_id=helper.id, delta=-1, reason="mentor_request"))

        db.commit()

    print("Demo hesaplar hazır:")
    print(f"  Ana (mentor+öğrenci) : {MAIN_EMAIL} / {MAIN_PW}")
    print(f"  Yardımcı mentor      : {HELPER_EMAIL} / {HELPER_PW}")


if __name__ == "__main__":
    seed()
