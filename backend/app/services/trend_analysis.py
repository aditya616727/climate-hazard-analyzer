"""Trend analysis: ordinary least-squares slope + first-vs-last-5yr change."""

import numpy as np

from app.models import TrendResult, YearlyStat


def analyze_trend(yearly: list[YearlyStat]) -> TrendResult:
    years = np.array([y.year for y in yearly], dtype=float)
    counts = np.array([y.heatwave_count for y in yearly], dtype=float)

    if len(years) < 3:
        return TrendResult(slope_per_year=0.0, pct_change_vs_baseline=None, trend_direction="flat")

    slope, _ = np.polyfit(years, counts, 1)
    if slope > 0.01:
        direction = "increasing"
    elif slope < -0.01:
        direction = "decreasing"
    else:
        direction = "flat"

    pct_change = None
    if len(counts) >= 10:
        first = counts[:5].mean()
        last = counts[-5:].mean()
        if first > 0:
            pct_change = round((last - first) / first * 100, 1)

    return TrendResult(
        slope_per_year=round(float(slope), 3),
        pct_change_vs_baseline=pct_change,
        trend_direction=direction,
    )


def headline(region_label: str, trend: TrendResult) -> str:
    if trend.pct_change_vs_baseline is None:
        return f"Not enough years in {region_label} to quantify the heatwave trend."
    pct = abs(trend.pct_change_vs_baseline)
    verb = "increased" if trend.trend_direction == "increasing" else "decreased"
    return (
        f"Heatwaves have {verb} by {pct}% in {region_label} "
        f"(first 5 vs last 5 years, {trend.slope_per_year:+.3f} events/year)."
    )
