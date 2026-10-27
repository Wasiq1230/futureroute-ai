from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    route_searches: int
    avg_eta_minutes: float
    avg_congestion_risk: float
    fuel_savings_liters: float
    top_corridors: list[dict]

