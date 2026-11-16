<p align="center">
  <img src="assets/brand/farmbits-icon.png" alt="" height="72">
  <img src="assets/brand/farmbits-wordmark.png" alt="FARMBITS" height="64">
</p>

<p align="center"><b>Your farm is changing. Your plan isn't.</b><br>
Team Canoa Espacial · NASA Space Apps Challenge 2026 · <i>Field Shift: Adapting Farms with NASA Data</i></p>

---

FARMBITS turns **30 years of NASA climate data into planting decisions for any farm on Earth**. A farmer taps their land on a map and sees:
- how their local climate has shifted;
- which crops are least likely to fail for lack of water;
- which 3-year crop rotation plans balance drought risk, soil health and financial return.

It works as a **web app** and as a **Telegram bot** that answers in the farmer's own language, by text or voice, and warns them before a drought hits their crop.

## The problem

The climate has shifted faster than traditional planting calendars. In **Rio Verde, Brazil**, comparing 1995–2009 with 2010–2025 (NASA POWER):

| Indicator | Before | After |
|---|---|---|
| Rainy-season rainfall | 1,351 mm | **1,086 mm (−20%)** |
| Days per year at 35 °C or more | 8 | **14.6** |
| Corn sown on Feb 15: seasons that ran short of water | 7 of 15 | **9 of 15** |

Farmers still decide with the calendar they inherited. The data that shows the change exists, but it never reaches the field.

## The solution

### Web app: four steps
1. **Where is your land:** tap the map, search for a city, or pick one of four demo sites (Rio Verde 🇧🇷, Nakuru 🇰🇪, Ludhiana 🇮🇳, Ames 🇺🇸).
2. **Your climate changed:** rainfall, rainy-season start and end, dry spells and extreme-heat days, before and after 2010.
3. **What to plant:** crops ranked for a sowing date by their crop-failure risk, simulated over 30 seasons. Priorities (return, drought safety, soil health) can be adjusted live.
4. **Rotation plans:** from the last three seasons planted, FARMBITS proposes 3-year plans and compares water risk, soil health and return side by side.

### Telegram bot: [@Farmbitsbot](https://t.me/Farmbitsbot)
- **Location:** a farmer shares their location and gets a climate summary and the best crop for today.
- **Questions:** they ask anything in their own words, by **text or voice**, in Portuguese, English or Spanish. The AI answers only through the engine's tools, so every number comes from the data.
- **Drought alerts:** `/alerta Milho 15/12/2026` subscribes to **proactive warnings before flowering**, checked daily against recent NASA POWER data.
- **Photos:** field photos are described by a vision model and appear on the web app's map.

Every answer cites its sources. When crop parameters are still generic, the app and the bot say so.

## How it works

```
NASA POWER (daily, 1995–2025) ──┐
SoilGrids (soil water)  ────────┼─► core/  Python engine, no UI
FAOSTAT (yield and price) ──────┤     • FAO-56 Penman-Monteith reference ET
FAO-56/66 (crop parameters) ────┘     • daily soil-water balance for every season
                                      • failure risk = seasons with yield loss above the limit
                                      • crop ranking and 3-year rotation plans
                                         │
          ┌──────────────────────────────┼──────────────────────────────┐
          ▼                              ▼                              ▼
   app.py (Streamlit web app)   mcp_server.py (MCP, token auth)  bot.py (Telegram + Groq)
   map, 4 steps, pt/en/es       8 engine tools                    text, voice, photos, alerts
                                         ▲                              │
                                         └──── the AI (Groq) calls ─────┘
         the web app and the bot share one SQLite database (farms, photos, alerts)
```

- **Climate:** NASA POWER (AG community). It provides bias-corrected precipitation (`PRECTOTCORR`), max and min temperature, solar radiation, humidity, wind, pressure and root-zone soil wetness. Responses are cached locally, and the four demo sites ship with the repo.
- **Soil water:** clay and sand from SoilGrids, converted with Saxton & Rawls (2006). If SoilGrids is down, the engine uses 100 mm of available water.
- **Crops:** 9 crops, with crop coefficients, growth stages, root depth and yield-response factor (`ky`) from FAO-56 and FAO-66 (`data/culturas.csv`).
- **Return:** yield × price per country from FAOSTAT (157 countries), discounted by the simulated average loss.
- **Brazil adapter:** `core/adaptadores/brasil.py` is a hook for municipal data. The global engine works anywhere without it.

## Run it locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your keys (.env is never committed)
```

| What | Command | Needs in `.env` |
|---|---|---|
| Web app | `streamlit run app.py` → http://localhost:8501 | nothing |
| MCP server | `python mcp_server.py` → http://127.0.0.1:8000/mcp | `MCP_TOKEN` |
| Telegram bot | `python bot.py` | `TELEGRAM_BOT_TOKEN`, `GROQ_API_KEY`, `MCP_TOKEN`, `MCP_PUBLIC_URL` |
| Tests | `pytest -q` | nothing (network and AI are mocked) |

The web app runs with no keys at all. On startup it precomputes the four demo sites in the background.

### Publishing the MCP server over HTTPS (needed by the bot)

Groq calls the engine tools through a public URL. Keep the MCP server on `127.0.0.1` and open a tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

1. Copy the generated address, with `/mcp` at the end, into `MCP_PUBLIC_URL`.
2. Set `MCP_STATELESS_HTTP=true`.
3. Start `mcp_server.py` and `bot.py`.

Requests without `Authorization: Bearer <MCP_TOKEN>` get `401`. A Quick Tunnel URL changes on every run: update `.env` and restart the server and the bot when it does. See [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

## Project layout

```
core/                 engine (no UI, bot or AI)
  power.py solo.py    data sources: NASA POWER and SoilGrids, with cache
  balanco.py          FAO-56 reference ET and water balance
  clima.py modelo.py  climate shift, crop ranking, planting window, rotation plans
  contexto.py pais.py global_ctx.py adaptadores/   country, hemisphere, FAOSTAT, Brazil adapter
  db.py alertas.py recente.py                      shared database and drought alerts
web/                  web app screens (map, location, results, translations)
bot_logica/           conversation, tools, AI, photos, audio, language, rate limit
app.py · bot.py · mcp_server.py
data/                 culturas.csv (crops), faostat.csv, paises.geojson (Natural Earth)
cache/                cached NASA POWER and SoilGrids responses
tests/                224 tests written from the acceptance criteria
.specs/               specs, tasks and verification records (spec-driven development)
```

Code identifiers are in Portuguese, the team's language. The web app and the bot speak Portuguese, English and Spanish.

## Known limitations

- **Generic crop parameters:** they come from FAO and are not yet calibrated per region. Both the web app and the bot say so.
- **Gross return:** return does not yet subtract production costs, so high-price crops (such as potato) can rank high despite high risk. Raising the "drought safety" priority fixes the order.
- **Unstable SoilGrids:** when it fails, the engine falls back to 100 mm of available soil water.
- **Two rainy seasons:** regions such as East Africa are modeled with one season per year for now.

## Open data used

- [NASA POWER](https://power.larc.nasa.gov/): daily climate since 1995, for any coordinate
- [SoilGrids (ISRIC)](https://soilgrids.org/): soil texture, 0–30 cm
- [FAO-56](https://www.fao.org/4/x0490e/x0490e00.htm) and FAO-66: evapotranspiration and crop parameters
- [FAOSTAT](https://www.fao.org/faostat/): yield and producer price by country
- [Natural Earth](https://www.naturalearthdata.com/): country boundaries
- [OpenStreetMap](https://www.openstreetmap.org/): base map and place search in the web app

## Team Canoa Espacial

Edvan · Matheus Francisco · Nascimento · Vinicius · Kaue · Cecilia, NASA Space Apps Recife 2026.
