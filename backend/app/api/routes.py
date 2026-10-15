"""API routes: health, analyze, AI insight, AI Q&A, CSV export."""

import csv
import io

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.ai.insights import ai_answer, ai_narrative
from app.db import get_db
from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    AskRequest,
    InsightRequest,
)
from app.services.hazard_detection import detect_heatwaves, percentile_threshold
from app.services.trend_analysis import analyze_trend, headline
from app.services.weather_client import cache_key, fetch_daily_max_temp

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/regions")
async def region_presets():
    """Preset regions so the UI works without a map on day one."""
    return [
        {"name": "Delhi, India", "box": {"lat_min": 28.4, "lat_max": 28.9, "lon_min": 76.8, "lon_max": 77.4}},
        {"name": "Mumbai, India", "box": {"lat_min": 18.9, "lat_max": 19.3, "lon_min": 72.7, "lon_max": 73.1}},
        {"name": "Ahmedabad, India", "box": {"lat_min": 22.9, "lat_max": 23.2, "lon_min": 72.4, "lon_max": 72.7}},
        {"name": "Phoenix, USA", "box": {"lat_min": 33.3, "lat_max": 33.7, "lon_min": -112.3, "lon_max": -111.9}},
        {"name": "Paris, France", "box": {"lat_min": 48.7, "lat_max": 49.0, "lon_min": 2.2, "lon_max": 2.6}},
    ]


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze(request: Request, body: AnalyzeRequest):
    # Auto-adjust baseline if it falls outside the selected year range
    bl_start = body.baseline_start
    bl_end = body.baseline_end
    if bl_start < body.start_year or bl_end > body.end_year:
        # Use first ~30% of the range, minimum 1 year
        span = body.end_year - body.start_year
        bl_start = body.start_year
        bl_end = body.start_year + max(1, span // 3)
        bl_end = min(bl_end, body.end_year)

    # Ensure we fetch data that covers both analysis range and baseline
    fetch_start = min(body.start_year, bl_start)
    fetch_end = max(body.end_year, bl_end)

    key = f"{cache_key(body.region, fetch_start, fetch_end)}|{body.hazard}"
    db = await get_db()
    cached = await db["analysis_cache"].find_one({"cache_key": key})
    if cached:
        cached.pop("_id", None)
        return AnalyzeResponse(**cached)

    df = await fetch_daily_max_temp(body.region, fetch_start, fetch_end)

    try:
        threshold = percentile_threshold(df, bl_start, bl_end)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail=f"No temperature data available for baseline period {bl_start}–{bl_end}. "
                   f"Try a wider year range.",
        )

    events, yearly, missing = detect_heatwaves(df, threshold)
    trend = analyze_trend(yearly)

    result = AnalyzeResponse(
        cache_key=key,
        threshold_c=round(threshold, 2),
        yearly=yearly,
        events=events,
        trend=trend,
        headline=headline("the selected region", trend),
        data_quality={"missing_days_by_year": {str(k): v for k, v in missing.items()}},
    )
    doc = result.model_dump()
    doc["cache_key"] = key
    await db["analysis_cache"].insert_one(doc)
    return result


@router.post("/ai/insight")
@limiter.limit("20/minute")
async def ai_insight(request: Request, body: InsightRequest):
    narrative = await ai_narrative(body.analysis, body.region_label)
    return {"narrative": narrative}


@router.post("/ai/ask")
@limiter.limit("20/minute")
async def ai_ask(request: Request, body: AskRequest):
    answer = await ai_answer(body.analysis, "the selected region", body.question)
    return {"answer": answer}


@router.post("/export/csv")
@limiter.limit("10/minute")
async def export_csv(request: Request, body: InsightRequest):
    """Bonus: CSV export of yearly stats + events."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["year", "heatwave_count", "heatwave_days", "longest_days", "max_temp_c"])
    for y in body.analysis.yearly:
        w.writerow([y.year, y.heatwave_count, y.heatwave_days, y.longest_days, y.max_temp_c])
    w.writerow([])
    w.writerow(["event_start", "event_end", "duration_days", "max_temp_c"])
    for e in body.analysis.events:
        w.writerow([e.start_date, e.end_date, e.duration_days, e.max_temp_c])
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=heatwave_analysis.csv"},
    )
