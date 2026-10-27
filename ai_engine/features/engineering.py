from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import math
import pandas as pd


FEATURE_COLUMNS = [
    "distance_km",
    "duration_minutes",
    "weather_risk",
    "mean_congestion",
    "incident_severity",
    "hour_sin",
    "hour_cos",
    "is_weekend",
    "route_index",
]


@dataclass(frozen=True)
class FeatureContext:
    departure_time: datetime | None = None


def temporal_features(moment: datetime | None = None) -> dict:
    now = moment or datetime.now(UTC)
    hour = now.hour + now.minute / 60
    return {
        "hour_sin": math.sin(2 * math.pi * hour / 24),
        "hour_cos": math.cos(2 * math.pi * hour / 24),
        "is_weekend": int(now.weekday() >= 5),
    }


def route_feature_frame(records: list[dict], context: FeatureContext | None = None) -> pd.DataFrame:
    context = context or FeatureContext()
    temporal = temporal_features(context.departure_time)
    rows = []
    for record in records:
        row = {column: 0 for column in FEATURE_COLUMNS}
        row.update({key: record.get(key, 0) for key in row})
        row.update(temporal)
        rows.append(row)
    return pd.DataFrame(rows, columns=FEATURE_COLUMNS)
