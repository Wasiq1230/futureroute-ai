from fastapi import APIRouter, Depends, Request
from backend.app.api.deps import limiter
from backend.app.core.security import get_current_user
from backend.app.schemas.route import RouteRequest, RouteResponse
from backend.app.services.routing import routing_service


router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/plan", response_model=RouteResponse)
@limiter.limit("45/minute")
async def plan_route(
    request: Request,
    payload: RouteRequest,
    user: str = Depends(get_current_user),
) -> RouteResponse:
    payload.user_id = payload.user_id or user
    return await routing_service.get_routes(payload)

