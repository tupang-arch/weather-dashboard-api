import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

async def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
        ],
        "hourly": [
            "temperature_2m",
            "apparent_temperature",
            "precipitation",
            "wind_speed_10m",
        ],
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(OPEN_METEO_URL, params=params)
        r.raise_for_status()
        return r.json()