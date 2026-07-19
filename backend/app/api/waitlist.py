"""Pazara çıkış bekleme listesi: herkese açık /join sayfası + kayıt ucu.

Sayfa backend'den servis edilir (legal.py /privacy deseni) — paylaşılacak link:
https://artapp-production.up.railway.app/join
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..core.messages import normalize_lang
from ..db import get_db
from ..models.tables import User, WaitlistSignup
from .mentors import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["waitlist"])


class SignupBody(BaseModel):
    email: EmailStr
    language: str = "tr"


@router.post("/waitlist")
def join_waitlist(body: SignupBody, db: Session = Depends(get_db)):
    """Auth'suz kayıt. Aynı e-posta ikinci kez gelirse sessizce 200 —
    sayfadan çifte tıklama hata göstermesin."""
    exists = db.execute(
        select(WaitlistSignup).where(WaitlistSignup.email == body.email.lower())
    ).scalar_one_or_none()
    if exists is None:
        db.add(
            WaitlistSignup(
                email=body.email.lower(), language=normalize_lang(body.language)
            )
        )
        db.commit()
    return {"ok": True}


@router.get("/admin/waitlist")
def list_waitlist(
    admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    rows = db.execute(
        select(WaitlistSignup).order_by(WaitlistSignup.created_at)
    ).scalars().all()
    return {
        "count": len(rows),
        "signups": [
            {"email": r.email, "language": r.language, "created_at": r.created_at.isoformat()}
            for r in rows
        ],
    }


_JOIN_HTML = """<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Artora — Bekleme Listesi</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 560px; margin: 3rem auto;
           padding: 0 1.25rem; line-height: 1.6; color: #222; }
    h1 { font-size: 1.8rem; margin-bottom: .25rem; }
    .tag { color: #6b21a8; font-weight: 600; }
    ul { padding-left: 1.2rem; }
    form { display: flex; gap: .5rem; margin: 1.5rem 0 .5rem; }
    input[type=email] { flex: 1; padding: .7rem .9rem; border: 1px solid #bbb;
                        border-radius: 8px; font-size: 1rem; }
    button { padding: .7rem 1.2rem; border: 0; border-radius: 8px; font-size: 1rem;
             background: #6b21a8; color: #fff; cursor: pointer; }
    #done { display: none; color: #15803d; font-weight: 600; }
    .en { color: #666; font-size: .85rem; margin-top: 2rem; }
  </style>
</head>
<body>
  <h1>Artora</h1>
  <p class="tag">Kendi kendine çizim öğrenenler için AI destekli mentor platformu</p>
  <p>Yıllarını yanlış yönde harcama. Artora seviyeni 3 çiziminden belirler,
     sana özel bir yetenek ağacında ilerletir ve her ödevine saniyeler içinde
     yapıcı, teknik AI analizi verir. Yetmezse gerçek mentorlar bir dokunuş uzakta.</p>
  <ul>
    <li>🎯 Seviyene göre kişisel ders yolu</li>
    <li>🖍️ Her ödeve anında redline analizi</li>
    <li>🧑‍🎨 Jetonla gerçek mentor geri bildirimi</li>
  </ul>
  <p><strong>Beta yakında.</strong> Erken erişim için listeye katıl:</p>
  <form id="f">
    <input type="email" id="email" placeholder="e-posta adresin" required>
    <button type="submit">Katıl</button>
  </form>
  <p id="done">Listedesin! Beta açılınca haber vereceğiz. 🎉</p>
  <p class="en"><em>Artora — an AI-powered mentor platform for self-taught artists.
     Join the waitlist above to get early access.</em></p>
  <script>
    document.getElementById('f').addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('email').value;
      const lang = (navigator.language || 'tr').startsWith('tr') ? 'tr' : 'en';
      try {
        await fetch('/waitlist', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({email: email, language: lang}),
        });
      } catch (err) { /* sessiz — tekrar denenebilir */ }
      document.getElementById('f').style.display = 'none';
      document.getElementById('done').style.display = 'block';
    });
  </script>
</body>
</html>
"""


@router.get("/join", response_class=HTMLResponse, include_in_schema=False)
def join_page() -> str:
    return _JOIN_HTML
