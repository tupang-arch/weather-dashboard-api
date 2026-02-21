from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.settings import settings
from app.services.weather_service import get_weather
from app.services.geocode_service import get_city_coords

app = FastAPI(title=settings.app_name)


class WeatherResponse(BaseModel):
    cached: bool
    data: dict = Field(..., description="Raw Open-Meteo response")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/weather", response_model=WeatherResponse)
async def weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    return await get_weather(lat, lon)


def _weather_icon(weather_code: int | None) -> str:
    """
    Open-Meteo weathercode reference:
    0 Clear, 1-3 Mainly clear/partly cloudy/overcast,
    45-48 Fog, 51-57 Drizzle, 61-67 Rain, 71-77 Snow,
    80-82 Rain showers, 95 Thunderstorm
    """
    if weather_code is None:
        return "❓"
    if weather_code == 0:
        return "☀️"
    if weather_code in (1, 2):
        return "🌤️"
    if weather_code == 3:
        return "☁️"
    if weather_code in (45, 48):
        return "🌫️"
    if 51 <= weather_code <= 57:
        return "🌦️"
    if 61 <= weather_code <= 67:
        return "🌧️"
    if 71 <= weather_code <= 77:
        return "❄️"
    if 80 <= weather_code <= 82:
        return "🌧️"
    if weather_code == 95:
        return "⛈️"
    return "🌡️"


def _safe_round(x, nd=1):
    try:
        if x is None:
            return None
        return round(float(x), nd)
    except Exception:
        return None


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>Weather by City</title>
    <style>
      :root{
        --bg1:#0b1020;
        --bg2:#111a33;
        --card: rgba(255,255,255,.08);
        --card2: rgba(255,255,255,.12);
        --text: rgba(255,255,255,.92);
        --muted: rgba(255,255,255,.65);
        --border: rgba(255,255,255,.14);
        --accent: #7c5cff;
        --accent2:#22c55e;
        --danger:#ef4444;
      }
      *{box-sizing:border-box}
      body{
        margin:0; min-height:100vh;
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
        color:var(--text);
        background:
          radial-gradient(1100px 700px at 20% 10%, rgba(124,92,255,.25), transparent 60%),
          radial-gradient(900px 700px at 85% 30%, rgba(34,197,94,.18), transparent 60%),
          linear-gradient(180deg, var(--bg1), var(--bg2));
        display:flex;
        align-items:center;
        justify-content:center;
        padding:28px;
      }
      .wrap{width: min(920px, 100%);}
      .top{
        display:flex; align-items:flex-end; justify-content:space-between; gap:16px;
        margin-bottom:18px;
      }
      .brand h1{margin:0; font-size:28px; letter-spacing:.2px}
      .brand p{margin:6px 0 0; color:var(--muted); font-size:14px}
      .pill{
        display:inline-flex; align-items:center; gap:8px;
        border:1px solid var(--border);
        background: rgba(255,255,255,.06);
        padding:8px 10px; border-radius:999px;
        color:var(--muted); font-size:13px;
      }
      .grid{
        display:grid;
        grid-template-columns: 1.2fr .8fr;
        gap:16px;
      }
      @media (max-width: 860px){
        .grid{grid-template-columns: 1fr}
      }
      .card{
        background: var(--card);
        border:1px solid var(--border);
        border-radius:18px;
        padding:18px;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 35px rgba(0,0,0,.25);
      }
      label{display:block; font-size:13px; color:var(--muted); margin:10px 0 6px}
      input{
        width:100%;
        padding:12px 12px;
        border-radius:12px;
        border:1px solid var(--border);
        background: rgba(0,0,0,.18);
        color:var(--text);
        outline:none;
      }
      input:focus{border-color: rgba(124,92,255,.55); box-shadow: 0 0 0 3px rgba(124,92,255,.18);}
      .row{display:grid; grid-template-columns: 1fr 160px; gap:10px}
      @media (max-width: 520px){ .row{grid-template-columns:1fr} }
      button{
        margin-top:12px;
        width:100%;
        padding:12px 14px;
        border-radius:14px;
        border:1px solid rgba(124,92,255,.55);
        background: linear-gradient(135deg, rgba(124,92,255,.9), rgba(124,92,255,.55));
        color:white;
        font-weight:700;
        cursor:pointer;
        transition: transform .05s ease;
      }
      button:active{transform: translateY(1px)}
      .hint{margin-top:10px; color:var(--muted); font-size:13px}
      .hint code{background: rgba(255,255,255,.08); padding:2px 6px; border-radius:8px; border:1px solid var(--border)}
      .mini{
        display:grid; gap:10px;
      }
      .mini .item{
        padding:12px;
        border-radius:14px;
        border:1px solid var(--border);
        background: rgba(255,255,255,.06);
      }
      .mini .item b{display:block; font-size:14px}
      .mini .item span{color:var(--muted); font-size:13px}
      .footer{
        margin-top:14px;
        color:var(--muted);
        font-size:12px;
      }
      .loading{
        display:none;
        margin-top:12px;
        padding:10px 12px;
        border-radius:14px;
        border:1px dashed rgba(255,255,255,.22);
        color:var(--muted);
        background: rgba(0,0,0,.12);
      }
      .dot{display:inline-block; width:7px; height:7px; border-radius:999px; background: var(--accent); margin-right:8px; animation: pulse 1.1s infinite;}
      @keyframes pulse{0%{opacity:.35}50%{opacity:1}100%{opacity:.35}}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="top">
        <div class="brand">
          <h1>Weather by City</h1>
          <p>Type a city, get the current temperature instantly (FastAPI + Open-Meteo).</p>
        </div>
        <div class="pill">⚡ Tip: try <b>&nbsp;Erfurt</b> + <b>&nbsp;DE</b></div>
      </div>

      <div class="grid">
        <div class="card">
          <form id="f" action="/city" method="get">
            <label>City</label>
            <input name="name" placeholder="Berlin" required />

            <div class="row">
              <div>
                <label>Country code (optional)</label>
                <input name="country_code" placeholder="DE" maxlength="2" />
              </div>
              <div>
                <label style="opacity:0">Search</label>
                <button type="submit">Search</button>
              </div>
            </div>

            <div id="loading" class="loading">
              <span class="dot"></span>Fetching weather...
            </div>

            <div class="hint">
              Examples: <code>Berlin</code> <code>Erfurt + DE</code> <code>Bucharest + RO</code>
            </div>
          </form>

          <div class="footer">
            Endpoints: <a style="color:rgba(255,255,255,.8)" href="/docs">/docs</a> ·
            Health: <a style="color:rgba(255,255,255,.8)" href="/health">/health</a>
          </div>
        </div>

        <div class="card mini">
          <div class="item">
            <b>What you’ll show on GitHub</b>
            <span>Clean architecture: clients/services + caching + validation + UI.</span>
          </div>
          <div class="item">
            <b>Next upgrade</b>
            <span>Deploy online + add hourly chart + autocomplete cities.</span>
          </div>
          <div class="item">
            <b>Pro move</b>
            <span>Add README + screenshots + badges.</span>
          </div>
        </div>
      </div>
    </div>

    <script>
      const f = document.getElementById('f');
      const loading = document.getElementById('loading');
      f.addEventListener('submit', () => {
        loading.style.display = 'block';
      });
    </script>
  </body>
</html>
"""


@app.get("/city", response_class=HTMLResponse)
async def weather_by_city(
    name: str = Query(..., min_length=2),
    country_code: str | None = Query(None, min_length=2, max_length=2),
):
    try:
        lat, lon, display = await get_city_coords(name, country_code=country_code)
        result = await get_weather(lat, lon)

        data = result.get("data") or {}
        current = data.get("current") or {}

        temp = _safe_round(current.get("temperature_2m"))
        wind = _safe_round(current.get("wind_speed_10m"))
        code = current.get("weather_code")
        icon = _weather_icon(code)

        cached = bool(result.get("cached"))

        # Some Open-Meteo setups may include these fields; if missing, we just show "-"
        apparent = _safe_round(current.get("apparent_temperature"))
        precip = _safe_round(current.get("precipitation"))

        badge = (
            '<span style="background:rgba(34,197,94,.18);border:1px solid rgba(34,197,94,.35);'
            'padding:6px 10px;border-radius:999px;color:rgba(255,255,255,.88);font-size:12px;">'
            'cached</span>'
            if cached
            else '<span style="background:rgba(124,92,255,.18);border:1px solid rgba(124,92,255,.35);'
                 'padding:6px 10px;border-radius:999px;color:rgba(255,255,255,.88);font-size:12px;">'
                 'live</span>'
        )

        if temp is None:
            return f"""
            <div style="font-family:Arial; margin:40px;">
              <h3>No temperature data for {display}</h3>
              <p><a href="/">Back</a></p>
            </div>
            """

        return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>{display} • Weather</title>
    <style>
      :root{{
        --bg1:#0b1020; --bg2:#111a33; --card: rgba(255,255,255,.08);
        --border: rgba(255,255,255,.14); --text: rgba(255,255,255,.92);
        --muted: rgba(255,255,255,.65); --accent:#7c5cff;
      }}
      *{{box-sizing:border-box}}
      body{{
        margin:0; min-height:100vh;
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
        color:var(--text);
        background:
          radial-gradient(1100px 700px at 20% 10%, rgba(124,92,255,.25), transparent 60%),
          radial-gradient(900px 700px at 85% 30%, rgba(34,197,94,.18), transparent 60%),
          linear-gradient(180deg, var(--bg1), var(--bg2));
        display:flex; align-items:center; justify-content:center;
        padding:28px;
      }}
      .card{{
        width: min(820px, 100%);
        background: var(--card);
        border:1px solid var(--border);
        border-radius:18px;
        padding:18px;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 35px rgba(0,0,0,.25);
      }}
      .top{{display:flex; justify-content:space-between; align-items:center; gap:14px}}
      h1{{margin:0; font-size:26px}}
      .sub{{margin:6px 0 0; color:var(--muted); font-size:14px}}
      .big{{font-size:54px; margin:18px 0 6px; letter-spacing:-.5px}}
      .grid{{display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; margin-top:14px}}
      @media (max-width:760px){{ .grid{{grid-template-columns:1fr}} }}
      .k{{padding:12px; border-radius:14px; border:1px solid var(--border); background: rgba(255,255,255,.06)}}
      .k b{{display:block; font-size:14px}}
      .k span{{color:var(--muted); font-size:13px}}
      a{{color:rgba(255,255,255,.86); text-decoration:none}}
      .actions{{margin-top:14px; display:flex; gap:10px; flex-wrap:wrap}}
      .btn{{padding:10px 12px; border-radius:12px; border:1px solid rgba(255,255,255,.18); background: rgba(0,0,0,.14)}}
    </style>
  </head>
  <body>
    <div class="card">
      <div class="top">
        <div>
          <h1>{display} {badge}</h1>
          <div class="sub">Lat {lat:.3f} • Lon {lon:.3f}</div>
        </div>
        <div style="font-size:34px;">{icon}</div>
      </div>

      <div class="big">{temp}°C</div>
      <div class="sub">Current temperature</div>

      <div class="grid">
        <div class="k"><b>Wind</b><span>{wind if wind is not None else "-"} km/h</span></div>
        <div class="k"><b>Feels like</b><span>{apparent if apparent is not None else "-"} °C</span></div>
        <div class="k"><b>Precipitation</b><span>{precip if precip is not None else "-"} mm</span></div>
      </div>

      <div class="actions">
        <a class="btn" href="/">← New search</a>
        <a class="btn" href="/docs">API Docs</a>
      </div>
    </div>
  </body>
</html>
"""
    except ValueError as e:
        return f"""
        <div style="font-family:Arial; margin:40px;">
          <h3>{str(e)}</h3>
          <p><a href="/">Back</a></p>
        </div>
        """