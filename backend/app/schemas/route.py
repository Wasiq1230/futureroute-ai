from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.common import Coordinate


class RouteRequest(BaseModel):
    source: Coordinate
    destination: Coordinate
    priority: str = Field(default="balanced", pattern="^(balanced|fastest|safest|fuel|emergency)$")
    departure_time: datetime | None = None
    user_id: str | None = None


class RouteStep(BaseModel):
    instruction: str
    distance_m: float
    duration_s: float


class RouteScore(BaseModel):
    ai_score: float
    eta_minutes: float
    eta_confidence: float
    congestion_risk: float
    safety_risk: float
    weather_risk: float
    fuel_liters: float
    explanation: list[str]


class RouteCandidate(BaseModel):
    id: str
    name: str
    geometry: list[Coordinate]
    distance_km: float
    duration_minutes: float
    score: RouteScore
    steps: list[RouteStep] = []


class RouteResponse(BaseModel):
    request_id: str
    best_route_id: str
    routes: list[RouteCandidate]
    traffic_heatmap: list[tuple[float, float, float]]
    incidents: list[dict]

