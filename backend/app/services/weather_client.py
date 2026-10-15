"""Ingestion from Open-Meteo ERA5 archive (free, no API key).

We query the archive API at the centroid of the requested bounding box
(to keep payloads small) and cache the raw daily series in MongoDB so
repeat requests never hit the external API again.
"""

import hashlib
from datetime import datetime

import httpx
import pandas as pd

from app.config import settings
from app.db import get_db
from app.models import RegionBox


def cache_key(bbox: RegionBox, start_year: int, end_year: int) -> str:
    raw = f"{bbox.lat_min},{bbox.lat_max},{bbox.lon_min},{bbox.lon_max}|{start_year}-{end_year}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def fetch_daily_max_temp(
    bbox: RegionBox, start_year: int, end_year: int
) -> pd.DataFrame:
    """Return DataFrame(date, tmax_c) with daily max temperature, cached in MongoDB."""
    key = cache_key(bbox, start_year, end_year)
    db = await get_db()
    cached = await db["weather_cache"].find_one(
        {"bbox": key, "start_year": start_year, "end_year": end_year}
    )
    if cached:
        df = pd.DataFrame(cached["series"])
        df["date"] = pd.to_datetime(df["date"])  # cache stores ISO strings
        df["tmax_c"] = pd.to_numeric(df["tmax_c"], errors="coerce")  # None -> NaN
        return df

    lat = (bbox.lat_min + bbox.lat_max) / 2
    lon = (bbox.lon_min + bbox.lon_max) / 2

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{start_year}-01-01",
        "end_date": f"{end_year}-12-31",
        "daily": "temperature_2m_max",
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(settings.open_meteo_archive_url, params=params)
        resp.raise_for_status()
        daily = resp.json()["daily"]

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(daily["time"]),
            "tmax_c": pd.to_numeric(daily["temperature_2m_max"], errors="coerce"),
        }
    ).dropna(subset=["date"]).reset_index(drop=True)

    # Persist cache (missing days stay NaN -> flagged as data gaps downstream)
    series = [
        {
            "date": d.isoformat() if isinstance(d, pd.Timestamp) else d,
            "tmax_c": None if pd.isna(v) else float(v),
        }
        for d, v in zip(df["date"], df["tmax_c"])
    ]
    await db["weather_cache"].insert_one(
        {
            "bbox": key,
            "start_year": start_year,
            "end_year": end_year,
            "fetched_at": datetime.utcnow(),
            "series": series,
        }
    )
    return df
