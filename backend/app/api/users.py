import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user, get_optional_user, get_request_lang
from ..core.messages import SUPPORTED_LANGUAGES, msg, normalize_lang
from ..core.ratelimit import rate_limit
from ..db import get_db
from ..models.tables import (
    AbilityScore,
    AiUsage,
    ContentReport,
    JetonTransaction,
    MentorProfile,
    MentorshipRequest,
    Purchase,
    Submission,
    User,
    UserProgress,
)
from ..services import jetons
from ..services.auth import (
    generate_token,
    hash_password,
    hash_token,
    verify_google_token,
    verify_password,
)
from ..services.storage import delete_drawing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


class GuestRequest(BaseModel):
    display_name: str = Field("Misafir Çizer", max_length=60)
    language: str = Field("", max_length=10)  # boşsa Accept-Language'ten


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)
    display_name: str = Field("Çizer", max_length=60)
    language: str = Field("", max_length=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class UpgradeRequest(BaseModel):
    """Misafir hesabını gerçek hesaba çevirir — ilerleme korunur."""

    email: EmailStr
    password: str = Field(max_length=128)


class AuthResponse(BaseModel):
    token: str
    id: int
    display_name: str
    is_guest: bool
    level: int
    xp: int
    language: str
    mentor_market_enabled: bool  # istemci mentor UI'ını buna göre gösterir


def _issue_token(user: User) -> str:
    """Yeni ham token üretir, hash'ini kullanıcıya yazar, hamı döndürür.
    Ham token yalnız bu yanıtta görünür — DB'de sadece hash durur."""
    raw = generate_token()
    user.api_token = hash_token(raw)
    return raw


def _auth_response(user: User, token: str = "") -> AuthResponse:
    """token: az önce üretilen HAM token. Token döndürmeyen akışlarda
    (dil değişikliği gibi) boş kalır — istemci bu alanı yalnız auth
    akışlarında kaydeder."""
    from ..core.config import get_settings

    return AuthResponse(
        token=token,
        id=user.id,
        display_name=user.display_name,
        is_guest=user.is_guest,
        level=user.level,
        xp=user.xp,
        language=user.language,
        mentor_market_enabled=get_settings().mentor_market_enabled,
    )


def _validate_password(password: str, lang: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=422, detail=msg("password_min", lang))


@router.post(
    "/guest",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit("auth_create", 20, 3600))],
)
def create_guest(
    body: GuestRequest,
    db: Session = Depends(get_db),
    lang: str = Depends(get_request_lang),
):
    user = User(
        display_name=body.display_name,
        is_guest=True,
        language=normalize_lang(body.language or lang),
    )
    raw_token = _issue_token(user)
    db.add(user)
    db.flush()
    jetons.grant_welcome(db, user)
    db.commit()
    return _auth_response(user, raw_token)


@router.post(
    "/register",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit("auth_create", 20, 3600))],
)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    lang: str = Depends(get_request_lang),
):
    lang = normalize_lang(body.language or lang)
    _validate_password(body.password, lang)
    exists = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail=msg("email_taken", lang))
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        is_guest=False,
        language=lang,
    )
    raw_token = _issue_token(user)
    db.add(user)
    db.flush()
    jetons.grant_welcome(db, user)
    db.commit()
    return _auth_response(user, raw_token)


@router.post(
    "/login",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit("login", 10, 900))],
)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    lang: str = Depends(get_request_lang),
):
    user = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if user is None or user.password_hash is None or not verify_password(
        body.password, user.password_hash
    ):
        raise HTTPException(status_code=401, detail=msg("login_failed", lang))
    # Her girişte token yenilenir (eski cihaz oturumu düşer — tek aktif token)
    raw_token = _issue_token(user)
    db.commit()
    return _auth_response(user, raw_token)


class GoogleRequest(BaseModel):
    id_token: str = Field(max_length=4096)
    language: str = Field("", max_length=10)


@router.post(
    "/google",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit("google", 20, 900))],
)
def google_sign_in(
    body: GoogleRequest,
    current: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
    lang: str = Depends(get_request_lang),
):
    """Google ile giriş/kayıt. Misafir token'ıyla çağrılırsa misafiri yükseltir
    (ilerleme korunur); yoksa google_sub/e-posta üzerinden bulur ya da oluşturur."""
    lang = normalize_lang(body.language or lang)
    try:
        info = verify_google_token(body.id_token)
    except ValueError:
        logger.exception("Google token doğrulaması başarısız")
        raise HTTPException(status_code=401, detail=msg("google_failed", lang))

    user = db.execute(
        select(User).where(User.google_sub == info["sub"])
    ).scalar_one_or_none()
    if user is None and info["email"]:
        # Aynı e-postayla kayıtlı hesabı Google'a bağla. info["email"] yalnız
        # Google e-postayı DOĞRULADIYSA doludur (auth.verify_google_token) —
        # doğrulanmamış e-postayla başkasının hesabı ele geçirilemez.
        user = db.execute(
            select(User).where(User.email == info["email"])
        ).scalar_one_or_none()
        if user is not None:
            user.google_sub = info["sub"]

    if user is None and current is not None and current.is_guest:
        # Misafir → Google hesabına yükselt, ilerleme korunur
        user = current
        user.google_sub = info["sub"]
        user.email = info["email"]
        user.display_name = info["name"]
        user.is_guest = False
    elif user is None:
        user = User(
            email=info["email"],
            google_sub=info["sub"],
            display_name=info["name"],
            is_guest=False,
            # Geçici değer (NOT NULL) — aşağıdaki _issue_token commit'ten önce yazar
            api_token=hash_token(generate_token()),
            language=lang,
        )
        db.add(user)
        db.flush()
        jetons.grant_welcome(db, user)

    raw_token = _issue_token(user)  # her girişte tek aktif token
    db.commit()
    return _auth_response(user, raw_token)


@router.delete("/me")
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Hesabı ve tüm verileri kalıcı siler (Play Store hesap silme şartı)."""
    submissions = db.execute(
        select(Submission).where(Submission.user_id == user.id)
    ).scalars().all()
    for s in submissions:
        try:
            delete_drawing(s.file_path)
        except Exception:
            logger.exception("Çizim dosyası silinemedi: %s", s.file_path)

    # Faz 2 temizliği — FK sırası: transaction'lar → istekler → profil.
    # Mentor olarak üstlendiği açık istekler: öğrencinin jetonu iade edilir,
    # kayıt mentor'suz kalır (öğrencinin geçmişi korunur).
    open_as_mentor = db.execute(
        select(MentorshipRequest).where(
            MentorshipRequest.mentor_id == user.id,
            MentorshipRequest.status == "assigned",
        )
    ).scalars().all()
    for r in open_as_mentor:
        student = db.get(User, r.student_id)
        if student is not None:
            jetons.refund(db, student, r)
        r.status = "expired"
    db.execute(
        MentorshipRequest.__table__.update()
        .where(MentorshipRequest.mentor_id == user.id)
        .values(mentor_id=None)
    )
    db.execute(delete(JetonTransaction).where(JetonTransaction.user_id == user.id))
    student_request_ids = select(MentorshipRequest.id).where(
        MentorshipRequest.student_id == user.id
    )
    db.execute(
        delete(JetonTransaction).where(JetonTransaction.request_id.in_(student_request_ids))
    )
    db.execute(delete(MentorshipRequest).where(MentorshipRequest.student_id == user.id))
    db.execute(delete(MentorProfile).where(MentorProfile.user_id == user.id))

    # Moderasyon kayıtları: kullanıcının yaptığı şikayetler + kendi gönderilerine
    # gelenler (FK sırası: submissions'tan önce silinmeli)
    own_submission_ids = select(Submission.id).where(Submission.user_id == user.id)
    db.execute(delete(ContentReport).where(ContentReport.reporter_id == user.id))
    db.execute(
        delete(ContentReport).where(ContentReport.submission_id.in_(own_submission_ids))
    )
    for table in (Submission, UserProgress, AbilityScore, AiUsage, Purchase):
        db.execute(delete(table).where(table.user_id == user.id))
    db.delete(user)
    db.commit()
    return {"deleted": True}


@router.post("/upgrade", response_model=AuthResponse)
def upgrade_guest(
    body: UpgradeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user.is_guest:
        raise HTTPException(status_code=409, detail=msg("already_registered", user.language))
    _validate_password(body.password, user.language)
    exists = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail=msg("email_taken", user.language))
    user.email = body.email
    user.password_hash = hash_password(body.password)
    user.is_guest = False
    # Token rotasyonu: istemci auth yanıtındaki yeni token'ı kaydeder
    raw_token = _issue_token(user)
    db.commit()
    return _auth_response(user, raw_token)


class DeviceUpdate(BaseModel):
    fcm_token: str = Field(max_length=256)  # kolon sınırıyla aynı — 500 yerine 422


@router.put("/me/device")
def register_device(
    body: DeviceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FCM cihaz token'ını kaydeder (tek cihaz — girişte üzerine yazılır)."""
    user.fcm_token = body.fcm_token.strip() or None
    db.commit()
    return {"ok": True}


class LanguageUpdate(BaseModel):
    language: str


@router.patch("/me/language", response_model=AuthResponse)
def update_language(
    body: LanguageUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Profildeki dil seçici: UI + AI çıktı dilini kalıcı değiştirir."""
    code = body.language.strip().lower()
    if code not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail=msg("language_unsupported", user.language))
    user.language = code
    db.commit()
    return _auth_response(user)
