from fastapi import APIRouter
from backend.app.schemas.analytics import AnalyticsSummary


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def summary() -> AnalyticsSummary:
    return AnalyticsSummary(
        route_searches=1284,
        avg_eta_minutes=23.8,
        avg_congestion_risk=0.41,
        fuel_savings_liters=318.4,
        top_corridors=[
            {"name": "Saddar to Blue Area", "volume": 342, "peak_risk": 0.78},
            {"name": "F-8 to Faisal Mosque", "volume": 215, "peak_risk": 0.51},
        ],
    )

