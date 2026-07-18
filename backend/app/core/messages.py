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
    # --- Faz 2: mentor pazarı ---
    "jeton_insufficient": {
        "tr": "Jetonun yetersiz — bu istek 1 jeton gerektiriyor.",
        "en": "Not enough jetons — this request costs 1 jeton.",
    },
    "no_mentor_available": {
        "tr": "Şu an müsait mentor yok — jetonun harcanmadı, biraz sonra tekrar dene.",
        "en": "No mentor is available right now — your jeton wasn't spent, try again soon.",
    },
    "mentor_request_exists": {
        "tr": "Bu ödev için zaten aktif bir mentor isteğin var.",
        "en": "You already have an active mentor request for this assignment.",
    },
    "mentor_not_found": {
        "tr": "Mentor bulunamadı",
        "en": "Mentor not found",
    },
    "request_not_found": {
        "tr": "İstek bulunamadı",
        "en": "Request not found",
    },
    "not_request_mentor": {
        "tr": "Bu istek sana atanmadı",
        "en": "This request isn't assigned to you",
    },
    "request_expired": {
        "tr": "Bu isteğin süresi dolmuş — öğrencinin jetonu iade edildi.",
        "en": "This request has expired — the student's jeton was refunded.",
    },
    "request_not_answered": {
        "tr": "Bu istek henüz cevaplanmadı",
        "en": "This request hasn't been answered yet",
    },
    "already_rated": {
        "tr": "Bu geri bildirimi zaten puanladın",
        "en": "You've already rated this feedback",
    },
    "rating_invalid": {
        "tr": "Puan 1 ile 5 arasında olmalı",
        "en": "Rating must be between 1 and 5",
    },
    "mentor_apply_exists": {
        "tr": "Zaten bir mentor başvurun var",
        "en": "You already have a mentor application",
    },
    "mentor_not_approved": {
        "tr": "Mentor hesabın henüz onaylanmadı",
        "en": "Your mentor account isn't approved yet",
    },
    "feedback_empty": {
        "tr": "Geri bildirim metni boş olamaz",
        "en": "Feedback text can't be empty",
    },
    "portfolio_not_yours": {
        "tr": "Portfolyoya yalnız kendi çizimlerini ekleyebilirsin",
        "en": "You can only add your own drawings to your portfolio",
    },
    "admin_only": {
        "tr": "Bu işlem için yetkin yok",
        "en": "You're not authorized for this action",
    },
    "application_not_found": {
        "tr": "Başvuru bulunamadı",
        "en": "Application not found",
    },
    # --- push bildirimleri (title|body çiftleri) ---
    "push_new_request_title": {
        "tr": "Yeni mentor isteği 🎨",
        "en": "New mentor request 🎨",
    },
    "push_new_request_body": {
        "tr": "{student} ödevine geri bildirim bekliyor — panelden inceleyebilirsin.",
        "en": "{student} is waiting for feedback on their assignment — check your panel.",
    },
    "push_feedback_ready_title": {
        "tr": "Ödevine mentor cevabı geldi!",
        "en": "Your mentor replied!",
    },
    "push_feedback_ready_body": {
        "tr": "{mentor} çizimini inceledi — geri bildirimi profilinden okuyabilirsin.",
        "en": "{mentor} reviewed your drawing — read the feedback in your profile.",
    },
    "push_request_refunded_title": {
        "tr": "Jetonun iade edildi",
        "en": "Your jeton was refunded",
    },
    "push_request_refunded_body": {
        "tr": "Mentor isteğin zamanında cevaplanamadı — 1 jeton hesabına geri yattı.",
        "en": "Your mentor request wasn't answered in time — 1 jeton was returned to you.",
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
