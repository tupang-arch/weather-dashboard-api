from app.clients.geocoding import geocode_city

async def get_city_coords(city: str, country_code: str | None = None) -> tuple[float, float, str]:
    data = await geocode_city(city, country_code=country_code)

    results = data.get("results") or []
    if not results:
        raise ValueError(f"City not found: {city}")

    top = results[0]
    lat = float(top["latitude"])
    lon = float(top["longitude"])
    display = f'{top.get("name", city)}, {top.get("country", "")}'.strip().strip(",")
    return lat, lon, display