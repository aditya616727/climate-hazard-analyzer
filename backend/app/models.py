from pydantic import BaseModel, Field, model_validator


class RegionBox(BaseModel):
    """Custom lat-lon bounding box."""

    lat_min: float = Field(ge=-90, le=90)
    lat_max: float = Field(ge=-90, le=90)
    lon_min: float = Field(ge=-180, le=180)
    lon_max: float = Field(ge=-180, le=180)

    @model_validator(mode="after")
    def check_order(self):
        if self.lat_min > self.lat_max or self.lon_min > self.lon_max:
            raise ValueError("min must be <= max for lat/lon bounds")
        return self


class AnalyzeRequest(BaseModel):
    region: RegionBox
    start_year: int = Field(default=1990, ge=1940, le=2024)
    end_year: int = Field(default=2020, ge=1941, le=2025)
    hazard: str = Field(default="heatwave")
    # Baseline years used to compute the 95th-percentile threshold
    baseline_start: int = Field(default=1990, ge=1940, le=2024)
    baseline_end: int = Field(default=1999, ge=1941, le=2025)

    @model_validator(mode="after")
    def check_years(self):
        if self.start_year > self.end_year:
            raise ValueError("start_year must be <= end_year")
        if self.baseline_start > self.baseline_end:
            raise ValueError("baseline_start must be <= baseline_end")
        return self


class HeatwaveEvent(BaseModel):
    start_date: str
    end_date: str
    duration_days: int
    max_temp_c: float


class YearlyStat(BaseModel):
    year: int
    heatwave_count: int
    heatwave_days: int
    longest_days: int
    max_temp_c: float | None


class TrendResult(BaseModel):
    slope_per_year: float
    pct_change_vs_baseline: float | None  # % change in event count, first vs last 5 yrs
    trend_direction: str  # "increasing" | "decreasing" | "flat"
    mann_kendall_p: float | None = None


class AnalyzeResponse(BaseModel):
    cache_key: str
    threshold_c: float
    yearly: list[YearlyStat]
    events: list[HeatwaveEvent]
    trend: TrendResult
    headline: str
    data_quality: dict  # gaps / missing days per year


class InsightRequest(BaseModel):
    analysis: AnalyzeResponse
    region_label: str = "this region"


class AskRequest(BaseModel):
    analysis: AnalyzeResponse
    question: str = Field(min_length=3, max_length=500)
