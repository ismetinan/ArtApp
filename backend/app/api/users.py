import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user, get_optional_user
from ..db import get_db
from ..models.tables import AbilityScore, AiUsage, Submission, User, UserProgress
from ..services.auth import (
    generate_token,
    hash_password,
    verify_google_token,
    verify_password,
)
from ..services.storage import delete_drawing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


class GuestRequest(BaseModel):
    display_name: str = "Misafir Çizer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str = "Çizer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpgradeRequest(BaseModel):
    """Misafir hesabını gerçek hesaba çevirir — ilerleme korunur."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    id: int
    display_name: str
    is_guest: bool
    level: int
    xp: int


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        token=user.api_token,
        id=user.id,
        display_name=user.display_name,
        is_guest=user.is_guest,
        level=user.level,
        xp=user.xp,
    )


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="Şifre en az 8 karakter olmalı")


@router.post("/guest", response_model=AuthResponse)
def create_guest(body: GuestRequest, db: Session = Depends(get_db)):
    user = User(display_name=body.display_name, is_guest=True, api_token=generate_token())
    db.add(user)
    db.commit()
    return _auth_response(user)


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    _validate_password(body.password)
    exists = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı")
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        is_guest=False,
        api_token=generate_token(),
    )
    db.add(user)
    db.commit()
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if user is None or user.password_hash is None or not verify_password(
        body.password, user.password_hash
    ):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı")
    # Her girişte token yenilenir (eski cihaz oturumu düşer — tek aktif token)
    user.api_token = generate_token()
    db.commit()
    return _auth_response(user)


class GoogleRequest(BaseModel):
    id_token: str


@router.post("/google", response_model=AuthResponse)
def google_sign_in(
    body: GoogleRequest,
    current: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Google ile giriş/kayıt. Misafir token'ıyla çağrılırsa misafiri yükseltir
    (ilerleme korunur); yoksa google_sub/e-posta üzerinden bulur ya da oluşturur."""
    try:
        info = verify_google_token(body.id_token)
    except ValueError:
        logger.exception("Google token doğrulaması başarısız")
        raise HTTPException(status_code=401, detail="Google girişi doğrulanamadı")

    user = db.execute(
        select(User).where(User.google_sub == info["sub"])
    ).scalar_one_or_none()
    if user is None and info["email"]:
        # Aynı e-postayla kayıtlı hesabı Google'a bağla
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
            api_token=generate_token(),
        )
        db.add(user)

    user.api_token = generate_token()  # her girişte tek aktif token
    db.commit()
    return _auth_response(user)


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
    for table in (Submission, UserProgress, AbilityScore, AiUsage):
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
        raise HTTPException(status_code=409, detail="Hesap zaten kayıtlı")
    _validate_password(body.password)
    exists = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı")
    user.email = body.email
    user.password_hash = hash_password(body.password)
    user.is_guest = False
    db.commit()
    return _auth_response(user)
