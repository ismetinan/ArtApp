"""Ortak API bağımlılıkları.

NOT: Kimlik doğrulama Faz 1 için bilinçli olarak basit tutuldu — istemci
X-User-Id başlığı gönderir (misafir akışı). Gerçek auth (e-posta + token)
Faz 2 öncesi eklenecek; tüm endpoint'ler bu dependency'den geçtiği için
değişiklik tek noktada olacak.
"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.tables import User


def get_current_user(
    x_user_id: int = Header(..., description="Misafir/kayıtlı kullanıcı id'si"),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, x_user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    return user
