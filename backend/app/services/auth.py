"""Parola hash'leme ve API token üretimi.

MVP yaklaşımı: kullanıcı başına tek aktif bearer token. Ham token yalnız
auth yanıtında istemciye döner; DB'de SHA-256 hash'i saklanır — DB sızıntısı
oturumları ele geçirmeye yetmez. JWT/refresh-token gerekirse ileride eklenir.
"""

import hashlib
import secrets

import bcrypt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from ..core.config import get_settings


def verify_google_token(token: str) -> dict:
    """Google ID token'ını doğrular; {sub, email, name} döner.

    email yalnız Google DOĞRULANMIŞ derse döner — doğrulanmamış e-posta,
    aynı adresle kayıtlı mevcut hesaba bağlanmakta kullanılamaz (hesap ele
    geçirme vektörü). Geçersiz/sahte token'da ValueError fırlatır.
    """
    client_id = get_settings().google_client_id
    if not client_id:
        raise ValueError("GOOGLE_CLIENT_ID yapılandırılmamış")
    info = google_id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
    verified = bool(info.get("email_verified"))
    return {
        "sub": info["sub"],
        "email": info.get("email") if verified else None,
        "name": info.get("name") or "Çizer",
    }


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def generate_token() -> str:
    return secrets.token_hex(32)


def hash_token(token: str) -> str:
    """DB'de saklanan biçim. SHA-256 yeterli: token 256 bit rastgele olduğundan
    bcrypt gibi yavaş hash gerekmez (sözlük/deneme saldırısı anlamsız)."""
    return hashlib.sha256(token.encode()).hexdigest()
