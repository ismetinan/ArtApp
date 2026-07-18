"""FCM push bildirimleri.

FIREBASE_SERVICE_ACCOUNT_JSON boşsa sessiz no-op (dev/test Firebase'siz çalışır).
send_push asla istisna fırlatmaz — bildirim, ana akışı (istek/feedback) hiçbir
koşulda bozamaz; hatalar loglanır.
"""

import json
import logging

from ..core.config import get_settings
from ..models.tables import User

logger = logging.getLogger(__name__)

_app = None
_init_failed = False


def _get_app():
    """Firebase Admin uygulamasını tembel başlatır; yapılandırma yoksa None."""
    global _app, _init_failed
    if _app is not None or _init_failed:
        return _app
    raw = get_settings().firebase_service_account_json
    if not raw:
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials

        cred = credentials.Certificate(json.loads(raw))
        _app = firebase_admin.initialize_app(cred)
    except Exception:
        logger.exception("Firebase init başarısız — push bildirimleri devre dışı")
        _init_failed = True
    return _app


def send_push(user: User, title: str, body: str) -> None:
    """Kullanıcının cihazına bildirim gönderir. Token yoksa / init yoksa no-op."""
    if user.fcm_token is None:
        return
    app = _get_app()
    if app is None:
        return
    try:
        from firebase_admin import messaging

        messaging.send(
            messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                token=user.fcm_token,
            ),
            app=app,
        )
    except Exception:
        # Geçersiz/expired token dahil: logla, akışı bozma
        logger.exception("Push gönderilemedi (user=%s)", user.id)
