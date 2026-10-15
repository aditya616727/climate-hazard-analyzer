"""Heatwave detection.

Definition (per the brief): 3+ consecutive days with daily max temperature
above the region's 95th percentile. The percentile is computed over a
baseline period (default: the first 10 years of the selected range).
"""

import pandas as pd

from app.models import HeatwaveEvent, YearlyStat


def percentile_threshold(df: pd.DataFrame, baseline_start: int, baseline_end: int) -> float:
    base = df[(df["date"].dt.year >= baseline_start) & (df["date"].dt.year <= baseline_end)]
    base = base.dropna(subset=["tmax_c"])
    if base.empty:
        raise ValueError("No baseline temperature data for the selected period")
    return float(base["tmax_c"].quantile(0.95))


def detect_heatwaves(
    df: pd.DataFrame, threshold_c: float, min_days: int = 3
) -> tuple[list[HeatwaveEvent], list[YearlyStat], dict[int, int]]:
    df = df.sort_values("date").reset_index(drop=True).copy()
    df["hot"] = df["tmax_c"] > threshold_c

    events: list[HeatwaveEvent] = []
    yearly: dict[int, YearlyStat] = {}
    missing: dict[int, int] = {}

    for year, g in df.groupby(df["date"].dt.year):
        year = int(year)
        missing[year] = int(g["tmax_c"].isna().sum())
        yearly[year] = YearlyStat(
            year=year,
            heatwave_count=0,
            heatwave_days=0,
            longest_days=0,
            max_temp_c=None if g["tmax_c"].dropna().empty else float(g["tmax_c"].max()),
        )

    # Find runs of consecutive hot days
    run_start, run_max = None, None
    dates = df["date"].tolist()
    for i, row in df.iterrows():
        if bool(row["hot"]):
            if run_start is None:
                run_start, run_max = dates[i], row["tmax_c"]
            else:
                run_max = max(run_max, row["tmax_c"])
        else:
            run_start, run_max = _flush_run(events, yearly, dates, i, run_start, run_max, min_days)

    # Flush trailing run
    _flush_run(events, yearly, dates, len(df), run_start, run_max, min_days)

    return events, list(yearly.values()), missing


def _flush_run(events, yearly, dates, i, run_start, run_max, min_days):
    if run_start is not None:
        duration = (dates[i - 1] - run_start).days + 1
        if duration >= min_days:
            year = int(run_start.year)
            events.append(
                HeatwaveEvent(
                    start_date=run_start.date().isoformat(),
                    end_date=dates[i - 1].date().isoformat(),
                    duration_days=duration,
                    max_temp_c=float(run_max),
                )
            )
            y = yearly[year]
            y.heatwave_count += 1
            y.heatwave_days += duration
            y.longest_days = max(y.longest_days, duration)
    return None, None
