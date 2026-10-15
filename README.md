# Climate Hazard Trend Analyzer

Full-stack case study for Dygnify Ventures: analyze historical heatwave trends for a
selected region and visualize them. Designed for ~8–10 hours of focused work.

## Live demo

- **App:** https://climate-hazard-analyzer-ten.vercel.app/
- **API:** https://climate-hazard-api-yl9o.onrender.com (`/api/health`, `/docs`)

## Deployment

- **Frontend → Vercel:** import the repo with project root `frontend/`;
  set `VITE_API_URL` to the Render backend URL (Production environment).
  A redeploy is required after changing it — Vite bakes env vars in at
  build time.
- **Backend → Render:** native Python runtime per `render.yaml`
  (rootDir `backend`, `uvicorn app.main:app`). Required env vars:
  `MONGO_URI` (MongoDB Atlas connection string — the app crash-loops
  without a reachable MongoDB) and `CORS_ORIGINS` (frontend origin).
  Optional: `OPENAI_API_KEY` + `INSIGHTS_MODE=openai` for LLM narratives;
  without them it falls back to deterministic template summaries.
- Render's free tier sleeps when idle — the first request after idle can
  take ~30–60s to wake the instance.

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
