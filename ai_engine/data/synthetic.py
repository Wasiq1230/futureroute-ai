from __future__ import annotations

import numpy as np
import pandas as pd


def build_synthetic_mobility_dataset(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    distance = rng.gamma(3.0, 4.0, rows).clip(1, 65)
    route_index = rng.integers(0, 3, rows)
    weather = rng.beta(1.8, 5.0, rows)
    rush = rng.choice([0.1, 0.4, 0.8], rows, p=[0.45, 0.35, 0.20])
    congestion = (0.18 + rush * 0.58 + rng.normal(0, 0.08, rows)).clip(0, 1)
    incidents = rng.exponential(0.08, rows).clip(0, 1)
    base_speed = 58 - 31 * congestion - 7 * weather - 5 * incidents - route_index * 1.5
    duration = (distance / np.maximum(12, base_speed) * 60 + rng.normal(0, 2.2, rows)).clip(2, 180)
    hour = rng.uniform(0, 24, rows)
    data = pd.DataFrame(
        {
            "distance_km": distance,
            "duration_minutes": duration,
            "weather_risk": weather,
            "mean_congestion": congestion,
            "incident_severity": incidents,
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
            "is_weekend": rng.integers(0, 2, rows),
            "route_index": route_index,
        }
    )
    data["eta_minutes"] = duration * (1 + 0.18 * congestion + 0.11 * weather + 0.08 * incidents)
    data["congestion_risk"] = congestion
    data["safety_risk"] = (0.22 + weather * 0.24 + incidents * 0.45 + route_index * 0.04).clip(0, 1)
    data["fuel_liters"] = (distance * (0.065 + 0.035 * congestion + 0.012 * weather)).clip(0.05, 20)
    data["ai_score"] = (
        35 * data["eta_minutes"] / data["eta_minutes"].max()
        + 28 * data["congestion_risk"]
        + 22 * data["safety_risk"]
        + 15 * data["fuel_liters"] / data["fuel_liters"].max()
    )
    return data

