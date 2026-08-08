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
    "upload_not_image": {
        "tr": "Dosya geçerli bir görsel değil — PNG, JPG veya WebP yükleyebilirsin",
        "en": "The file isn't a valid image — you can upload PNG, JPG or WebP",
    },
    "request_too_large": {
        "tr": "İstek çok büyük",
        "en": "Request is too large",
    },
    "rate_limited": {
        "tr": "Çok fazla deneme yapıldı — lütfen biraz bekleyip tekrar dene.",
        "en": "Too many attempts — please wait a bit and try again.",
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
        "tr": "Jetonun yetersiz — bu istek {cost} jeton gerektiriyor.",
        "en": "Not enough jetons — this request costs {cost} jeton(s).",
    },
    "gold_insufficient": {
        "tr": "Seçmeli mentor {cost} altın jeton gerektiriyor — ücretsiz jetonlar yalnız havuzda geçerli. Mağazadan altın jeton alabilirsin.",
        "en": "Choosing a mentor costs {cost} gold jetons — free jetons only work for the pool. You can buy gold jetons in the store.",
    },
    "no_mentor_available": {
        "tr": "Şu an müsait mentor yok — jetonun harcanmadı, biraz sonra tekrar dene.",
        "en": "No mentor is available right now — your jeton wasn't spent, try again soon.",
    },
    # --- Asenkron analiz işleri (Faz 2, 2026-08-08) ---
    "analysis_in_progress": {
        "tr": "Zaten devam eden bir analizin var. O bitince yenisini gönderebilirsin.",
        "en": "You already have an analysis in progress. You can send another once it finishes.",
    },
    "job_not_found": {
        "tr": "Bu analiz bulunamadı.",
        "en": "That analysis couldn't be found.",
    },
    # --- Jeton = AI ekonomisi (2026-08-08) ---
    # AI harcaması için ayrı çift: eski jeton_insufficient mentor isteği metnidir
    # ("bu istek"), canlı Android'de kullanılıyor ve dokunulmuyor.
    "jeton_insufficient_ai": {
        "tr": "Bu analiz için {cost} jeton gerekiyor. Haftalık ücretsiz jetonlarının yenilenmesini bekleyebilir ya da mağazadan jeton alabilirsin.",
        "en": "This analysis costs {cost} jeton(s). You can wait for your weekly free jetons to renew, or buy jetons in the store.",
    },
    "jeton_insufficient_no_store": {
        "tr": "Bu analiz için {cost} jeton gerekiyor. Ücretsiz jetonların her hafta yenileniyor.",
        "en": "This analysis costs {cost} jeton(s). Your free jetons renew every week.",
    },
    "too_many_open_requests": {
        "tr": "Aynı anda en fazla {count} açık mentor isteğin olabilir. Mevcut isteklerinden biri cevaplanınca yenisini gönderebilirsin.",
        "en": "You can have at most {count} open mentor requests at a time. Once one of them is answered you can send another.",
    },
    "mentor_cooldown": {
        "tr": "Bu mentora 24 saat içinde tekrar soru soramazsın. Başka bir mentor seçebilir ya da havuza sorabilirsin.",
        "en": "You can't ask this mentor again within 24 hours. You can pick another mentor or ask the pool.",
    },
    "mentor_busy": {
        "tr": "Bu mentorun kutusu şu an dolu. Daha sonra tekrar dene ya da havuza sor.",
        "en": "This mentor's inbox is full right now. Try again later or ask the pool.",
    },
    "donation_url_invalid": {
        "tr": "Bağış bağlantısı desteklenen platformlardan biri olmalı: Kreosus, Shopier, Papara, Patreon, Ko-fi, Buy Me a Coffee.",
        "en": "The donation link must be from a supported platform: Kreosus, Shopier, Papara, Patreon, Ko-fi, Buy Me a Coffee.",
    },
    "no_payment_details_in_text": {
        "tr": "Metin alanlarına IBAN veya kart bilgisi yazılamaz. Ödeme almak için bağış bağlantısı alanını kullan.",
        "en": "IBAN or card details can't be written in text fields. Use the donation link field to receive support.",
    },
    "sample_critique_too_short": {
        "tr": "Örnek kritik en az {count} karakter olmalı — mentorluk kalitesini böyle değerlendiriyoruz.",
        "en": "Your sample critique must be at least {count} characters — this is how we assess mentoring quality.",
    },
    "mentor_rules_not_accepted": {
        "tr": "Başvurmak için mentor kurallarını kabul etmen gerekiyor.",
        "en": "You need to accept the mentor rules before applying.",
    },
    "reapply_too_soon": {
        "tr": "Başvurun reddedildikten sonra {days} gün beklemen gerekiyor. Bu sürede portfolyonu güçlendirebilirsin.",
        "en": "You need to wait {days} days after a rejected application. Use the time to strengthen your portfolio.",
    },
    "mentor_request_exists": {
        "tr": "Bu ödev için zaten aktif bir mentor isteğin var.",
        "en": "You already have an active mentor request for this assignment.",
    },
    "mentor_unavailable": {
        "tr": "Bu mentor şu an yeni istek almıyor — başka bir mentor seç ya da havuzu dene.",
        "en": "This mentor isn't taking new requests right now — pick another or try the pool.",
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
    "content_unsafe": {
        "tr": "Bu görsel topluluk kurallarına uygun görünmediği için paylaşılamıyor. Bir hata olduğunu düşünüyorsan Profil'deki geri bildirim butonundan bize yaz.",
        "en": "This image can't be shared because it doesn't appear to follow the community guidelines. If you think this is a mistake, contact us via the feedback button in your Profile.",
    },
    "moderation_blocked": {
        "tr": "Bu çizim topluluk kuralları gereği kaldırıldı ve yeniden paylaşılamaz. Bir hata olduğunu düşünüyorsan bize yaz.",
        "en": "This drawing was removed under the community guidelines and can't be shared again. If you think this is a mistake, contact us.",
    },
    "share_level_locked": {
        "tr": "Topluluğa paylaşım {level}. seviyede açılıyor. Derslerinle ilerledikçe çizimlerini herkese açabileceksin — çizimlerin şu an sende özel olarak duruyor.",
        "en": "Sharing to the community unlocks at level {level}. As you progress through the lessons you'll be able to make your drawings public — for now they stay private to you.",
    },
    "free_analysis_limit": {
        "tr": "Bu haftaki serbest analiz hakkını kullandın — haftaya yenilenir. Premium'da serbest analiz sınırsız.",
        "en": "You've used this week's free analysis — it renews next week. Free analysis is unlimited with Premium.",
    },
    # --- Play Billing ---
    "purchase_invalid": {
        "tr": "Satın alma doğrulanamadı. Ödeme gerçekleştiyse endişelenme — 'Satın alımları geri yükle' ile tekrar deneyebilirsin.",
        "en": "The purchase couldn't be verified. If you were charged, don't worry — try again with 'Restore purchases'.",
    },
    "billing_unavailable": {
        "tr": "Mağaza şu an kullanılamıyor, lütfen daha sonra tekrar dene.",
        "en": "The store is currently unavailable, please try again later.",
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
        "tr": "Mentor isteğin zamanında cevaplanamadı — {count} jeton hesabına geri yattı.",
        "en": "Your mentor request wasn't answered in time — {count} jeton(s) were returned to you.",
    },
    # Ücretsiz mentorlukta iade edilecek jeton yok — bu yüzden ayrı çift
    "push_request_expired_title": {
        "tr": "Mentor isteğin zaman aşımına uğradı",
        "en": "Your mentor request timed out",
    },
    "push_request_expired_body": {
        "tr": "Mentor isteğin zamanında cevaplanamadı. Dilersen tekrar gönderebilirsin.",
        "en": "Your mentor request wasn't answered in time. Feel free to send it again.",
    },
    # Analiz arka planda bittiğinde — kullanıcı uygulamadan çıkmış olabilir,
    # asıl mesele bu (senkron akışta çıkarsa sonucu hiç göremiyordu)
    "push_analysis_ready_title": {
        "tr": "Analizin hazır",
        "en": "Your analysis is ready",
    },
    "push_analysis_ready_body": {
        "tr": "Çizimine yapay zekâ geri bildirimi geldi — bakmak için dokun.",
        "en": "AI feedback on your drawing is in — tap to take a look.",
    },
    "push_analysis_failed_title": {
        "tr": "Analiz tamamlanamadı",
        "en": "The analysis couldn't be completed",
    },
    "push_analysis_failed_body": {
        "tr": "Bir sorun çıktı ve jetonun iade edildi. Tekrar deneyebilirsin.",
        "en": "Something went wrong and your jeton was refunded. Feel free to try again.",
    },
    "push_application_approved_title": {
        "tr": "Mentor başvurun onaylandı 🎉",
        "en": "Your mentor application was approved 🎉",
    },
    "push_application_approved_body": {
        "tr": "Artık mentorsun! Profilindeki Mentor Paneli'nden istekleri alabilirsin.",
        "en": "You're a mentor now! You can receive requests from the Mentor Panel in your profile.",
    },
    "push_application_rejected_title": {
        "tr": "Mentor başvurun hakkında",
        "en": "About your mentor application",
    },
    "push_application_rejected_body": {
        "tr": "Bu seferlik onaylayamadık — profilini güncelleyip yeniden başvurabilirsin.",
        "en": "We couldn't approve it this time — you can update your profile and apply again.",
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
