from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Climate Hazard Trend Analyzer"
    debug: bool = False

    # NoSQL database (MongoDB)
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "climate_hazards"

    # Open-Meteo ERA5 archive endpoint (free, no API key needed)
    open_meteo_archive_url: str = "https://archive-api.open-meteo.com/v1/archive"

    # Optional: OpenAI-compatible API key powers the AI narrative/Q&A features.
    # Without it the API falls back to deterministic, stats-only summaries.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Rate limiting (per minute)
    rate_limit: str = "30/minute"


settings = Settings()
