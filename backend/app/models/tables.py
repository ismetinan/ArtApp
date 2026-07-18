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
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    # Faz 1'de altyapı var ama harcama akışı yok (CLAUDE.md Faz 1 kapsamı)
    jeton_balance: Mapped[int] = mapped_column(Integer, default=0)
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


class AbilityScore(Base):
    __tablename__ = "ability_scores"
    __table_args__ = (UniqueConstraint("user_id", "axis"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    axis: Mapped[str] = mapped_column(String(32))
    score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    user: Mapped[User] = relationship(back_populates="ability_scores")
