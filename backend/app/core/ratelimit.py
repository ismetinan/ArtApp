"""Girişsiz uçlar için IP başına basit hız limiti (brute-force/spam koruması).

Tek instance'lı beta için bellek içi kayan pencere yeterli — Redis'e taşımak
Faz 4 ölçekleme konusu. Railway proxy'si gerçek istemci IP'sini
X-Forwarded-For'un SONUNA ekler; istemcinin kendi gönderdiği sahte girdiler
listenin başında kalır, bu yüzden son eleman alınır.
"""

import time
from collections import deque

from fastapi import HTTPException, Request

from .config import get_settings
from .messages import msg, negotiate_lang

_BUCKETS: dict[tuple[str, str], deque[float]] = {}
_MAX_KEYS = 20_000  # bellek emniyeti — dolarsa süresi geçmiş kayıtlar atılır


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "?"


def _prune(now: float, window: float) -> None:
    for key in [k for k, q in _BUCKETS.items() if not q or q[-1] <= now - window]:
        del _BUCKETS[key]


def rate_limit(scope: str, limit: int, window_seconds: int):
    """Dependency üretir: aynı IP'den pencere içinde limit aşılırsa 429."""

    def dependency(request: Request) -> None:
        if not get_settings().rate_limit_enabled:
            return
        now = time.monotonic()
        key = (scope, _client_ip(request))
        bucket = _BUCKETS.get(key)
        if bucket is None:
            if len(_BUCKETS) >= _MAX_KEYS:
                _prune(now, window_seconds)
            bucket = _BUCKETS[key] = deque()
        while bucket and bucket[0] <= now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            lang = negotiate_lang(request.headers.get("accept-language"))
            raise HTTPException(status_code=429, detail=msg("rate_limited", lang))
        bucket.append(now)

    return dependency
