"""Kullanıcıya dönük API mesajlarının dil kataloğu (tr/en).

Yalnız HTTP `detail` gibi kullanıcıya gösterilen metinler burada; iç loglar ve
istisnalar çevrilmez. Dil seçimi: girişli isteklerde `users.language`, girişsiz
isteklerde `Accept-Language` başlığı (bkz. negotiate_lang).
"""

SUPPORTED_LANGUAGES = ("tr", "en")
DEFAULT_LANGUAGE = "tr"

_CATALOG: dict[str, dict[str, str]] = {
    # --- auth / users ---
    "session_missing": {
        "tr": "Oturum bulunamadı",
        "en": "No session found",
    },
    "session_invalid": {
        "tr": "Geçersiz oturum",
        "en": "Invalid session",
    },
    "password_min": {
        "tr": "Şifre en az 8 karakter olmalı",
        "en": "Password must be at least 8 characters",
    },
    "email_taken": {
        "tr": "Bu e-posta zaten kayıtlı",
        "en": "This e-mail is already registered",
    },
    "login_failed": {
        "tr": "E-posta veya şifre hatalı",
        "en": "Wrong e-mail or password",
    },
    "google_failed": {
        "tr": "Google girişi doğrulanamadı",
        "en": "Google sign-in could not be verified",
    },
    "already_registered": {
        "tr": "Hesap zaten kayıtlı",
        "en": "Account is already registered",
    },
    "language_unsupported": {
        "tr": "Desteklenmeyen dil — tr veya en seçilebilir",
        "en": "Unsupported language — choose tr or en",
    },
    # --- onboarding / dersler ---
    "need_three_drawings": {
        "tr": "Tam olarak 3 çizim yüklenmeli",
        "en": "Exactly 3 drawings must be uploaded",
    },
    "node_not_found": {
        "tr": "Ders bulunamadı",
        "en": "Lesson not found",
    },
    "node_locked": {
        "tr": "Bu dersin önkoşulları henüz tamamlanmadı",
        "en": "This lesson's prerequisites are not completed yet",
    },
    # --- AI ---
    "ai_unavailable": {
        "tr": "AI şu an yanıt veremiyor, lütfen birazdan tekrar dene.",
        "en": "The AI can't respond right now, please try again in a bit.",
    },
    "ai_quota_exhausted": {
        "tr": (
            "Bugünlük AI analiz hakkın doldu — yarın yeni haklarla devam "
            "edebilirsin. Bu arada çizim pratiğine devam!"
        ),
        "en": (
            "You've used today's AI analysis quota — you can continue with "
            "fresh credits tomorrow. Keep practicing in the meantime!"
        ),
    },
    # --- upload / galeri ---
    "upload_unsupported_type": {
        "tr": "Desteklenmeyen dosya türü: {suffix}",
        "en": "Unsupported file type: {suffix}",
    },
    "upload_too_large": {
        "tr": "Dosya çok büyük — en fazla 8 MB yükleyebilirsin",
        "en": "File is too large — the maximum is 8 MB",
    },
    "submission_not_found": {
        "tr": "Gönderi bulunamadı",
        "en": "Submission not found",
    },
    "file_not_found": {
        "tr": "Dosya bulunamadı",
        "en": "File not found",
    },
}


def normalize_lang(value: str | None) -> str:
    """Herhangi bir dil değerini desteklenen koda indirger (bilinmeyen → tr)."""
    if value:
        code = value.strip().lower()[:2]
        if code in SUPPORTED_LANGUAGES:
            return code
    return DEFAULT_LANGUAGE


def negotiate_lang(accept_language: str | None) -> str:
    """Accept-Language başlığından desteklenen ilk dili seçer.

    Basit ayrıştırma yeterli: "en-US,en;q=0.9,tr;q=0.8" → en.
    """
    if not accept_language:
        return DEFAULT_LANGUAGE
    for part in accept_language.split(","):
        code = part.split(";")[0].strip().lower()[:2]
        if code in SUPPORTED_LANGUAGES:
            return code
    return DEFAULT_LANGUAGE


def msg(key: str, lang: str, **fmt: object) -> str:
    entry = _CATALOG[key]
    text = entry.get(normalize_lang(lang), entry[DEFAULT_LANGUAGE])
    return text.format(**fmt) if fmt else text
