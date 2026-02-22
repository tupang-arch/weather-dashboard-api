import os

import httpx
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from app.settings import settings
from app.services.geocode_service import get_city_coords
from app.services.weather_service import get_weather

app = FastAPI(title=settings.app_name)


def _home_page(error: str | None = None, result_html: str | None = None) -> str:
    err = f"<p style='color:#ff6b6b;'><b>{error}</b></p>" if error else ""
    res = result_html or ""
    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Weather by City</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 24px;
      background: #0b1220;
      color: #e6e6e6;
    }}
    .card {{
      max-width: 560px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }}
    h1 {{ margin-top: 0; }}
    p {{ line-height: 1.5; }}
    label {{ display:block; margin-top: 10px; opacity: 0.95; }}
    input {{
      width: 100%;
      padding: 12px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.18);
      background: rgba(0,0,0,0.25);
      color: #fff;
      margin-top: 6px;
      box-sizing: border-box;
      font-size: 16px;
    }}
    button {{
      margin-top: 14px;
      padding: 12px 16px;
      border-radius: 12px;
      border: none;
      background: #7c5cff;
      color: white;
      font-weight: 700;
      cursor: pointer;
      width: 100%;
      font-size: 16px;
    }}
    small {{ opacity: 0.75; }}
    .result {{
      margin-top: 16px;
      padding: 14px;
      border-radius: 12px;
      background: rgba(0,0,0,0.25);
      border: 1px solid rgba(255,255,255,0.12);
    }}
    a {{ color: #9fd3ff; }}
    code {{
      background: rgba(255,255,255,0.08);
      padding: 2px 6px;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,0.10);
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Weather by City</h1>
    <p>Type a city and get the current temperature instantly (FastAPI + Open-Meteo).</p>

    {err}

    <form action="/city" method="get">
      <label>City</label>
      <input name="name" placeholder="Berlin" required minlength="2" />

      <label>Country code (optional)</label>
      <input name="country_code" placeholder="DE" />

      <button type="submit">Search</button>
      <small>Examples: <code>Erfurt</code> + <code>DE</code>, <code>Bucharest</code> + <code>RO</code></small>
    </form>

    {res}

    <p style="margin-top:14px;">
      API Docs: <a href="/docs">/docs</a> • Health: <a href="/health">/health</a>
    </p>
  </div>
</body>
</html>
"""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(_home_page())


@app.get("/city", response_class=HTMLResponse)
async def city_weather(
    name: str = Query(..., min_length=2),
    country_code: str | None = Query(None),
):
    try:
        lat, lon, display = await get_city_coords(name, country_code)
        result = await get_weather(lat, lon)

        data = result.get("data", result)
        current = data.get("current") or {}

        temp = current.get("temperature_2m")
        wind = current.get("wind_speed_10m")

        if temp is None:
            return HTMLResponse(_home_page(error="No temperature data returned by provider."))

        cached = bool(result.get("cached", False))
        stale = bool(result.get("stale", False))

        mode = "Live"
        if cached and stale:
            mode = "Cached (stale)"
        elif cached:
            mode = "Cached"

        result_html = f"""
        <div class="result">
          <h2 style="margin:0 0 8px 0;">{display}</h2>
          <p style="margin:0;"><b>Temperature now:</b> {temp} °C</p>
          <p style="margin:6px 0 0 0;"><b>Wind:</b> {wind} km/h</p>
          <p style="margin:10px 0 0 0; opacity:0.8;">
            Mode: {mode} • Coords: {lat:.4f}, {lon:.4f}
          </p>
          <p style="margin:10px 0 0 0; opacity:0.75; font-size:13px;">
            If you see rate-limit messages, wait 1–2 minutes (provider limits on free/shared hosting).
          </p>
        </div>
        """
        return HTMLResponse(_home_page(result_html=result_html))

    except ValueError as e:
        return HTMLResponse(_home_page(error=str(e)))

    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response else 500

        if status == 429:
            return HTMLResponse(
                _home_page(
                    error="Rate limit (429) from Open-Meteo. Please wait 1–2 minutes and try again. "
                         "On free/shared hosting, limits can happen even with few users."
                )
            )

        return HTMLResponse(_home_page(error=f"Provider error: HTTP {status}"))

    except Exception as e:
        return HTMLResponse(_home_page(error=f"Internal error: {str(e)}"))


# Local run helper (Render uses $PORT)
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)