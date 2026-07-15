"""Ortak API bağımlılıkları.

Kimlik doğrulama: Authorization: Bearer <token>. Token, kullanıcı başına tek
aktif olacak şekilde DB'de saklanır (users.api_token). Tüm endpoint'ler bu
dependency'den geçer — auth şeması değişirse tek nokta burası.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.tables import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Oturum bulunamadı")
    user = db.execute(
        select(User).where(User.api_token == credentials.credentials)
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Geçersiz oturum")
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Token varsa kullanıcıyı döner, yoksa None — /users/google gibi hem
    girişsiz hem misafir-yükseltme olarak çalışan endpoint'ler için."""
    if credentials is None:
        return None
    return db.execute(
        select(User).where(User.api_token == credentials.credentials)
    ).scalar_one_or_none()
