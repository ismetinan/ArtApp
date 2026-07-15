"""Parola hash'leme ve API token üretimi.

MVP yaklaşımı: kullanıcı başına tek aktif, DB'de saklanan bearer token.
JWT/refresh-token karmaşası Faz 2'de gerekirse eklenir.
"""

import secrets

import bcrypt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from ..core.config import get_settings


def verify_google_token(token: str) -> dict:
    """Google ID token'ını doğrular; {sub, email, name} döner.

    Geçersiz/sahte token'da ValueError fırlatır (google-auth davranışı).
    """
    client_id = get_settings().google_client_id
    if not client_id:
        raise ValueError("GOOGLE_CLIENT_ID yapılandırılmamış")
    info = google_id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
    return {
        "sub": info["sub"],
        "email": info.get("email"),
        "name": info.get("name") or "Çizer",
    }


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def generate_token() -> str:
    return secrets.token_hex(32)
