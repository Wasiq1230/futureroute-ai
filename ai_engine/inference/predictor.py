from __future__ import annotations

from pathlib import Path
import joblib
import numpy as np
from ai_engine.features.engineering import FEATURE_COLUMNS, FeatureContext, route_feature_frame


class MobilityPredictor:
    def __init__(self, artifact_dir: str = "ai_engine/artifacts") -> None:
        self.artifact_dir = Path(artifact_dir)
        self.models = self._load_models()

    def _load_models(self) -> dict:
        models = {}
        for target in ["eta_minutes", "congestion_risk", "safety_risk", "fuel_liters", "ai_score"]:
            path = self.artifact_dir / f"{target}.joblib"
            if path.exists():
                models[target] = joblib.load(path)
        return models

    def predict_route(self, record: dict) -> dict:
        frame = route_feature_frame([record], FeatureContext())
        if self.models:
            raw = {target: float(model.predict(frame[FEATURE_COLUMNS])[0]) for target, model in self.models.items()}
        else:
            raw = self._deterministic_fallback(record)
        priority = record.get("priority", "balanced")
        raw["ai_score"] = self._priority_adjusted_score(raw, priority)
        raw["eta_confidence"] = round(float(np.clip(1 - raw["congestion_risk"] * 0.35 - raw["weather_risk"] * 0.25, 0.52, 0.96)), 3)
        raw["explanation"] = self._explain(raw, record)
        return {
            "ai_score": round(raw["ai_score"], 2),
            "eta_minutes": round(raw["eta_minutes"], 1),
            "eta_confidence": raw["eta_confidence"],
            "congestion_risk": round(raw["congestion_risk"], 3),
            "safety_risk": round(raw["safety_risk"], 3),
            "weather_risk": round(raw["weather_risk"], 3),
            "fuel_liters": round(raw["fuel_liters"], 2),
            "explanation": raw["explanation"],
        }

    def _deterministic_fallback(self, record: dict) -> dict:
        distance = float(record["distance_km"])
        duration = float(record["duration_minutes"])
        congestion = float(record.get("mean_congestion", 0.35))
        weather = float(record.get("weather_risk", 0.2))
        incidents = float(record.get("incident_severity", 0.0))
        eta = duration * (1 + congestion * 0.18 + weather * 0.10 + incidents * 0.05)
        safety = min(1.0, 0.18 + weather * 0.26 + incidents * 0.42 + record.get("route_index", 0) * 0.04)
        fuel = distance * (0.068 + congestion * 0.03 + weather * 0.01)
        score = eta * 0.55 + congestion * 16 + safety * 14 + fuel * 2.2
        return {
            "eta_minutes": eta,
            "congestion_risk": congestion,
            "safety_risk": safety,
            "weather_risk": weather,
            "fuel_liters": fuel,
            "ai_score": score,
        }

    def _priority_adjusted_score(self, raw: dict, priority: str) -> float:
        weights = {
            "balanced": (0.42, 0.24, 0.22, 0.12),
            "fastest": (0.68, 0.16, 0.08, 0.08),
            "safest": (0.28, 0.18, 0.44, 0.10),
            "fuel": (0.28, 0.20, 0.12, 0.40),
            "emergency": (0.76, 0.16, 0.05, 0.03),
        }.get(priority, (0.42, 0.24, 0.22, 0.12))
        return (
            weights[0] * raw["eta_minutes"]
            + weights[1] * raw["congestion_risk"] * 100
            + weights[2] * raw["safety_risk"] * 100
            + weights[3] * raw["fuel_liters"] * 8
        )

    def _explain(self, raw: dict, record: dict) -> list[str]:
        notes = []
        if raw["congestion_risk"] < 0.4:
            notes.append("Low predicted congestion across sampled road segments.")
        else:
            notes.append("Congestion risk is material; ETA includes a delay buffer.")
        if raw["weather_risk"] > 0.35:
            notes.append("Weather conditions increase route risk and ETA uncertainty.")
        if raw["safety_risk"] < 0.35:
            notes.append("Safety model rates this corridor as comparatively stable.")
        notes.append(f"Fuel estimate is based on {record.get('distance_km', 0):.1f} km and congestion-adjusted consumption.")
        return notes

