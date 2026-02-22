import time
import httpx
from cachetools import TTLCache

from app.settings import settings
from app.clients.open_meteo import fetch_weather

# Cache "fresh" (normal)
_fresh_cache = TTLCache(maxsize=512, ttl=settings.cache_ttl_seconds)

# Cache "stale" (ultima valoare bună, păstrată mai mult)
_stale_cache = TTLCache(maxsize=512, ttl=max(settings.cache_ttl_seconds * 6, 3600))  # min 1h

# Cooldown global când primim 429 ca să nu mai lovim API-ul o perioadă
_cooldown_until = 0.0


def _key(lat: float, lon: float) -> str:
    # rotunjim ca să evităm chei diferite pentru diferențe minuscule
    return f"{lat:.3f}:{lon:.3f}"


async def get_weather(lat: float, lon: float) -> dict:
    global _cooldown_until

    k = _key(lat, lon)

    # 1) dacă avem fresh, returnăm imediat
    if k in _fresh_cache:
        return {"cached": True, "stale": False, "data": _fresh_cache[k]}

    # 2) dacă suntem în cooldown (după 429), nu mai chemăm provider-ul
    now = time.time()
    if now < _cooldown_until:
        if k in _stale_cache:
            return {"cached": True, "stale": True, "data": _stale_cache[k]}
        # dacă nu avem nimic salvat, propagăm o eroare controlată
        raise httpx.HTTPStatusError(
            "Rate limit cooldown (no cached data available).",
            request=None,
            response=type("Resp", (), {"status_code": 429})(),
        )

    # 3) încercăm să luăm live
    try:
        data = await fetch_weather(lat, lon)
        _fresh_cache[k] = data
        _stale_cache[k] = data
        return {"cached": False, "stale": False, "data": data}

    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response else 500

        # dacă e 429, intrăm în cooldown și servim stale dacă avem
        if status == 429:
            _cooldown_until = time.time() + 90  # 90 secunde pauză
            if k in _stale_cache:
                return {"cached": True, "stale": True, "data": _stale_cache[k]}
        raise