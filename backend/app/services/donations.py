"""Bağış bağlantısı doğrulama (2026-08-08 kararı).

Mentora ödeme uygulama DIŞINDA, %100 mentora giden isteğe bağlı bağışla oluyor;
Artora para akışına hiç girmez ve komisyon almaz. Apple §3.2.1 kişi-kişiye
hediyeye üç şartla izin veriyor: (1) tamamen isteğe bağlı, (2) %100 alıcıya,
(3) uygulamada hiçbir şeyi açmıyor. Bu modül (2) ve (3) için değil, güven/
dolandırıcılık tarafı için var: linkin nereye gittiğini sınırlar.

Neden beyaz liste: mentorun rastgele bir siteye link vermesi, öğrenciyi kimlik
avı sayfasına götürebilir. Ayrıca serbest metinde IBAN paylaşımı yasak — o hem
takip edilemez bir ödeme yolu hem de "önce öde sonra bakarım" pazarlığının
kapısı, ki bu Apple'ın 1. şartını da ihlal eder.

Platform seçimi Türkiye gerçeğine göre: Ko-fi ve Buy Me a Coffee payout için
PayPal ya da Stripe zorunlu tutuyor (BMC açıkça "yalnız Stripe ülkeleri"),
Türkiye ikisinde de yok → Türkiyeli mentor o ikisinden para ÇEKEMEZ. Bu yüzden
yerli/çalışan seçenekler önce geliyor; Ko-fi/BMC yalnız yurt dışı mentorlar için.
"""

import re
from urllib.parse import urlparse

# host → kullanıcıya gösterilecek platform adı. Tam host eşleşmesi aranır
# (alt yol serbest); "kreosus.com.saldirgan.net" gibi son ek oyunlarını engeller.
ALLOWED_DONATION_HOSTS: dict[str, str] = {
    # Türkiye'den para çekilebilen seçenekler
    "kreosus.com": "Kreosus",
    "www.kreosus.com": "Kreosus",
    "shopier.com": "Shopier",
    "www.shopier.com": "Shopier",
    "papara.com": "Papara",
    "www.papara.com": "Papara",
    "patreon.com": "Patreon",
    "www.patreon.com": "Patreon",
    # Yurt dışı mentorlar (TR'den payout alınamaz — bkz. modül docstring)
    "ko-fi.com": "Ko-fi",
    "www.ko-fi.com": "Ko-fi",
    "buymeacoffee.com": "Buy Me a Coffee",
    "www.buymeacoffee.com": "Buy Me a Coffee",
}

# TR IBAN'ı (TR + 24 hane) ve genel IBAN kalıbı; araya boşluk/nokta serpilmiş
# hallerini de yakalasın diye ayraçlar temizlendikten sonra aranır.
_IBAN_RE = re.compile(r"\bTR\d{24}\b|\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
# 13-19 haneli kart numarası
_CARD_RE = re.compile(r"\b\d{13,19}\b")
_SEPARATORS = re.compile(r"[\s.\-_/]")


class DonationUrlError(Exception):
    """Bağlantı beyaz listede değil ya da https değil."""


class PaymentDetailsInTextError(Exception):
    """Serbest metinde IBAN/kart bilgisi var."""


def normalize_donation_url(raw: str | None) -> tuple[str | None, str | None]:
    """(url, platform_adı) döner. Boş/None girdi → (None, None) = bağış linki yok.

    https zorunlu (http bağış linki kimlik avına açık kapı) ve host beyaz listede
    olmalı. Aksi halde DonationUrlError."""
    if raw is None:
        return None, None
    url = raw.strip()
    if not url:
        return None, None
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise DonationUrlError("https zorunlu")
    platform = ALLOWED_DONATION_HOSTS.get((parsed.hostname or "").lower())
    if platform is None:
        raise DonationUrlError("host beyaz listede değil")
    return url, platform


def ensure_no_payment_details(*texts: str | None) -> None:
    """Serbest metinlerde IBAN/kart numarası varsa PaymentDetailsInTextError.

    Ayraçlar temizlenerek aranır: "TR12 3456 ..." de "TR12.3456..." de yakalanır."""
    for text in texts:
        if not text:
            continue
        flat = _SEPARATORS.sub("", text).upper()
        if _IBAN_RE.search(flat) or _CARD_RE.search(flat):
            raise PaymentDetailsInTextError("metinde ödeme bilgisi var")
