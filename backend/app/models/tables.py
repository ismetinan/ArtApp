from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Google Sign-In: ID token'daki kalıcı "sub" kimliği (e-posta değişse de sabit)
    google_sub: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    api_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100), default="Misafir Çizer")
    is_guest: Mapped[bool] = mapped_column(Boolean, default=True)
    # UI + AI çıktı dili (tr/en) — cihaz locale'inden gelir, profilden değiştirilebilir
    language: Mapped[str] = mapped_column(String(5), default="tr")
    # FCM cihaz token'ı — tek-cihaz oturum modeliyle tutarlı tek token
    fcm_token: Mapped[str | None] = mapped_column(String(256), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    # Faz 2: mentor istekleri jetonla; beta'da satın alma yok, hoşgeldin jetonu var
    jeton_balance: Mapped[int] = mapped_column(Integer, default=0)
    # Mentor başvurularını onaylayan hesap (beta'da SQL ile bir kez atanır)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    # Premium abonelik bitişi (Play Billing) — None/geçmiş = ücretsiz katman
    premium_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    ability_scores: Mapped[list["AbilityScore"]] = relationship(back_populates="user")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="user")
    progress: Mapped[list["UserProgress"]] = relationship(back_populates="user")


class SkillNode(Base):
    """Yetenek ağacı düğümü. Faz 1'de statik seed verisiyle doldurulur."""

    __tablename__ = "skill_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # slug
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    # EN çeviriler (i18n) — boşsa TR'ye düşülür
    title_en: Mapped[str] = mapped_column(String(200), default="")
    description_en: Mapped[str] = mapped_column(Text, default="")
    youtube_video_id: Mapped[str] = mapped_column(String(20), default="")
    skill_axis: Mapped[str] = mapped_column(String(32))  # ai.schemas.SkillAxis değeri
    xp_reward: Mapped[int] = mapped_column(Integer, default=50)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)  # node id listesi
    # [{kind: video|playlist, youtube_id, title, author}] — art_sources.md müfredatı
    resources: Mapped[list] = mapped_column(JSON, default=list)


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (UniqueConstraint("user_id", "node_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    node_id: Mapped[str] = mapped_column(ForeignKey("skill_nodes.id"))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship(back_populates="progress")


class Submission(Base):
    """Yüklenen çizim + AI analizi. 'Gelişim Macerası' galerisinin veri kaynağı."""

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    node_id: Mapped[str | None] = mapped_column(ForeignKey("skill_nodes.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(16))  # onboarding | assignment
    file_path: Mapped[str] = mapped_column(String(500))
    ai_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Varsayılan: özel (CLAUDE.md §8 açık soruydu — güvenli taraf seçildi)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    # Moderasyon: admin gizlediyse sahibi yeniden herkese açık YAPAMAZ (UGC politikası)
    moderation_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="submissions")


class AiUsage(Base):
    """Kullanıcı başına günlük AI çağrı sayacı (beta kotası — OpenRouter ücretsiz
    katmanını bir avuç kullanıcının tüketmesini engeller)."""

    __tablename__ = "ai_usage"
    __table_args__ = (UniqueConstraint("user_id", "day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    day: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD (UTC)
    count: Mapped[int] = mapped_column(Integer, default=0)


class MentorProfile(Base):
    """Faz 2: mentor başvurusu/profili. Portfolyo, mentorun KENDİ galeri
    gönderilerinden seçilir (seçilenler public yapılır) — ayrı upload yok."""

    __tablename__ = "mentor_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    bio: Mapped[str] = mapped_column(Text, default="")
    styles: Mapped[list] = mapped_column(JSON, default=list)  # ör. ["manga", "realist"]
    portfolio_submission_ids: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|approved|rejected
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship()


class MentorshipRequest(Base):
    """1 jetonluk havuz isteği: ödev → rastgele müsait mentor → metin geri bildirim.
    48 saat cevapsız kalırsa erişim anında expired + jeton iadesi (tembel kontrol)."""

    __tablename__ = "mentorship_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    mentor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    jeton_cost: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="assigned")  # assigned|answered|expired
    feedback_text: Mapped[str] = mapped_column(Text, default="")
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5, öğrenci verir
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    submission: Mapped[Submission] = relationship()


class JetonTransaction(Base):
    """Jeton hareket kaydı — bakiye değişimi her zaman bir satırla belgelenir
    (para/güven akışı, CLAUDE.md §6)."""

    __tablename__ = "jeton_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    delta: Mapped[int] = mapped_column(Integer)  # +hoşgeldin/iade, -harcama
    reason: Mapped[str] = mapped_column(String(24))  # welcome|mentor_request|refund
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("mentorship_requests.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Assignment(Base):
    """AI'ın kullanıcıya özel ürettiği ödev görevi — düğüm başına bir kez üretilir,
    sonraki okumalar kota harcamaz."""

    __tablename__ = "assignments"
    __table_args__ = (UniqueConstraint("user_id", "node_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    node_id: Mapped[str] = mapped_column(ForeignKey("skill_nodes.id"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class WaitlistSignup(Base):
    """Pazara çıkış bekleme listesi (/join sayfasından, auth'suz)."""

    __tablename__ = "waitlist_signups"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    language: Mapped[str] = mapped_column(String(5), default="tr")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ContentReport(Base):
    """Topluluk galerisi şikayeti (Play UGC politikası: bildir + kaldır akışı).
    Kullanıcı başına gönderi başına tek şikayet — spam engeli."""

    __tablename__ = "content_reports"
    __table_args__ = (UniqueConstraint("submission_id", "reporter_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(32))  # uygunsuz | spam | telif | diger
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Purchase(Base):
    """Play Billing satın alma kaydı. purchase_token unique — aynı satın almanın
    ikinci kez hak vermesini engeller (para/güven akışı, CLAUDE.md §6)."""

    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[str] = mapped_column(String(64))
    purchase_token: Mapped[str] = mapped_column(String(512), unique=True)
    kind: Mapped[str] = mapped_column(String(16))  # jeton | subscription
    state: Mapped[str] = mapped_column(String(16), default="granted")
    # Abonelikte: jetonu verilmiş son fatura döneminin bitişi (dönem başına tek hak)
    granted_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AbilityScore(Base):
    __tablename__ = "ability_scores"
    __table_args__ = (UniqueConstraint("user_id", "axis"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    axis: Mapped[str] = mapped_column(String(32))
    score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    user: Mapped[User] = relationship(back_populates="ability_scores")
