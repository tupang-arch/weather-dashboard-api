import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

async def geocode_city(name: str, country_code: str | None = None) -> dict:
    params = {
        "name": name,
        "count": 1,
        "language": "en",
        "format": "json",
    }
    if country_code:
        params["country_code"] = country_code

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(GEOCODING_URL, params=params)
        r.raise_for_status()
        return r.json()