"""Async MongoDB client (Motor). NoSQL store for cached weather + analysis results."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

_client: AsyncIOMotorClient | None = None


async def get_db() -> AsyncIOMotorDatabase:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client[settings.mongo_db]


async def ensure_indexes() -> None:
    db = await get_db()
    # Cache lookups: one doc per (bbox, date range) weather pull
    await db["weather_cache"].create_index(
        ["bbox", "start_year", "end_year"], unique=True
    )
    # Analysis results cached per request signature
    await db["analysis_cache"].create_index("cache_key", unique=True)
