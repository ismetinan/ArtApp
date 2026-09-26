"""İstemci analitik olayları (2026-09).

Yalnız beyaz listedeki adlar kabul edilir; props içerik taşımamalı (düğüm id'si,
ürün id'si, kaynak ekran gibi kısa etiketler). Serbest metin, e-posta, çizim
asla gelmez — gelse bile uzunluk/tip kısıtları keser.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.messages import msg
from ..core.ratelimit import hit
from ..db import get_db
from ..models.tables import AppEvent, User
from .deps import get_current_user

router = APIRouter(tags=["events"])

ALLOWED_EVENTS = frozenset(
    {
        "lesson_opened",
        "video_opened",
        "assignment_generated",
        "store_opened",
        "purchase_started",
        "share_public",
        "mentor_request_sent",
        "gallery_opened",
        "free_analysis_opened",
    }
)
_ALLOWED_PROP_KEYS = frozenset({"node_id", "product_id", "source", "tab"})
_MAX_PROP_LEN = 64


class EventIn(BaseModel):
    name: str = Field(max_length=40)
    props: dict[str, str | int | bool] = Field(default_factory=dict)


def _clean_props(props: dict) -> dict:
    out = {}
    for k, v in props.items():
        if k not in _ALLOWED_PROP_KEYS:
            continue
        if isinstance(v, str):
            v = v[:_MAX_PROP_LEN]
        out[k] = v
    return out


@router.post("/events", status_code=204)
def log_event(
    body: EventIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.name not in ALLOWED_EVENTS:
        raise HTTPException(status_code=422, detail=msg("invalid_event", user.language))
    # Kullanıcı başına dakikada 60 olay — hatalı bir istemci döngüsü tabloyu
    # şişirmesin
    hit("events", f"u{user.id}", 60, 60, user.language)
    db.add(AppEvent(user_id=user.id, name=body.name, props=_clean_props(body.props)))
    db.commit()
