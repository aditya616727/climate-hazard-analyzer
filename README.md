# Climate Hazard Trend Analyzer

Full-stack case study for Dygnify Ventures: analyze historical heatwave trends for a
selected region and visualize them. Designed for ~8–10 hours of focused work.

## Quick start

```bash
# 1. Start MongoDB
docker compose up -d

# 2. Backend (Python 3.11+)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: add OPENAI_API_KEY for AI features
uvicorn app.main:app --reload   # -> http://localhost:8000/docs

# 3. Frontend (Node 18+)
cd ../frontend
npm install
npm run dev                  # -> http://localhost:5173
```

## Architecture

```
frontend (React + Vite + Chart.js)
    |  POST /api/analyze {region box, years, hazard}
backend (FastAPI)
    |-- services/weather_client.py  Open-Meteo ERA5 archive -> MongoDB cache
    |-- services/hazard_detection.py 95th-percentile heatwave rule
    |-- services/trend_analysis.py  OLS slope + first-vs-last-5yr % change
    |-- ai/insights.py  LLM narrative + Q&A (graceful fallback without API key)
    |-- api/routes.py  /health /regions /analyze /ai/* /export/csv
MongoDB: weather_cache (raw series), analysis_cache (computed results)
```

## Data source

**Open-Meteo ERA5 archive** (Copernicus ERA5 reanalysis served via open API —
no key, no signup, suitable for the case-study budget). One request per
region-year-range at the bounding-box centroid; raw series cached in MongoDB so
the external API is hit only once per region. Missing days are kept as gaps and
surfaced in `data_quality` instead of being silently imputed.

## Hazard logic (heatwave)

- Baseline = first 10 years of the range (configurable): threshold = 95th
  percentile of daily max temperature in the baseline.
- A heatwave = 3+ consecutive days with tmax above that threshold.
- Trend = least-squares slope of yearly event counts + % change between the
  first-5-year and last-5-year means. Direction is "increasing" / "decreasing" /
  "flat" on a ±0.01 events/year deadband.

## AI features

1. **AI Insight** (`POST /api/ai/insight`) — turns the verified stats into a
   plain-language briefing. The LLM only *explains* numbers computed in Python;
   prompts forbid inventing numbers, causes, or predictions. Without an
   `OPENAI_API_KEY` it degrades to a deterministic template summary, so the
   feature is demo-able everywhere.
2. **Ask the data** (`POST /api/ai/ask`) — chat Q&A grounded strictly on the
   computed analysis ("Which year had the longest heatwave?"). The model must
   answer only from the injected facts and say so when it can't.

## Assumptions

- Bounding-box centroid represents the region (documented trade-off; a proper
  spatial average is listed under improvements).
- ERA5 reanalysis ~31 km grid is fine for trend direction, not for exact local extremes.
- Heatwave = heatwave only; drought/heavy-rain detectors would follow the same
  interface and plug into `hazard_detection.py`.
- Rate limits (slowapi) + Pydantic validation guard the external API; MongoDB
  caching gives idempotent, cheap repeat analysis.

## Evaluation mapping

| Dimension (weight) | How this addresses it |
|---|---|
| Data handling (20%) | Missing-day gaps tracked per year, unit-safe °C pipeline, MongoDB caching |
| Climate logic (20%) | Percentile-based, baseline-relative heatwave definition |
| Backend (20%) | Clean FastAPI routers, async ingestion, rate limiting, input validation |
| Frontend (15%) | Interactive Chart.js time series, region presets + custom box |
| Critical thinking (10%) | Honest headlines ("flat trend" when flat), gaps surfaced, grounded AI |
| Security + perf (15%) | slowapi limits, validated inputs, cached external calls |
| Bonus (+10) | CSV export implemented; Leaflet map + Mann-Kendall = next steps |

## What I'd improve with more time

- Leaflet map UI for drawing the region box (bonus).
- Mann-Kendall significance test on the trend (bonus).
- Drought + heavy-rainfall detectors behind the same interface.
- Spatial averaging over the box instead of the centroid.
- Redis TTL cache layer in front of Mongo for hot regions.

## Verified end-to-end (real data)

The pipeline was executed against the live Open-Meteo ERA5 archive for
**Delhi, India** (28.4–28.9°N, 76.8–77.4°E, 1990–2020):

- 11,323 daily records, **0 missing days**
- Threshold: **41.6°C** (95th percentile of the 1990–1999 baseline)
- **62 heatwave events** detected (cross-checked with an independent
  brute-force run detector: 62/62 match)
- Longest: **22 days** (28 May – 18 Jun 1995, peak 46.4°C); worst year: 2010
- Headline: *"Heatwaves have decreased by 50.0% in the selected region
  (first 5 vs last 5 years, −0.027 events/year)."*
- The decreasing signal is present in the raw series itself (May–Jun mean
  tmax slope −0.027°C/yr; hot-days/yr fell from 19.8 to 8.4), and the
  direction is unchanged with a full-period percentile baseline — so it is a
  property of the ERA5 data at this grid point, not a code artifact.
- Second identical request served from MongoDB cache in **0.015 s**;
  `/api/ai/insight` template fallback, `/api/ai/ask` fallback, `/api/export/csv`,
  and 422 validation on bad inputs all verified.

## AI tools used

- **Muse (Meta)** generated the initial project scaffold and boilerplate
  (this README, FastAPI routers, React components, AI prompt constraints).
- A follow-up agent session then executed the pipeline end-to-end against real
  data (see "Verified end-to-end" above) and fixed the bugs it found:
  ISO-string date coercion and NaN handling on the MongoDB cache-read path,
  a missing slowapi 429 exception handler, and unused imports. (One issue was
  environment-only: the sandbox's `NO_PROXY` contains bare IPv6 entries that
  httpx 0.28 fails to parse; the app itself honors proxies correctly.)
- I reviewed the domain logic (heatwave definition, trend math, caching
  strategy, prompt grounding rules) and the fixes above, and can walk through
  the code and modify it live in the interview.
