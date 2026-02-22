from cachetools import TTLCache
from app.settings import settings
from app.clients.open_meteo import fetch_weather

_cache = TTLCache(maxsize=512, ttl=settings.cache_ttl_seconds)

def _cache_key(lat: float, lon: float) -> str:
    # rotunjim ca să nu facem cache diferit pentru 50.978700 vs 50.978701
    return f"{lat:.3f}:{lon:.3f}"

async def get_weather(lat: float, lon: float) -> dict:
    key = _cache_key(lat, lon)

    if key in _cache:
        return {"cached": True, "data": _cache[key]}

    data = await fetch_weather(lat, lon)
    _cache[key] = data
    return {"cached": False, "data": data}