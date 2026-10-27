from fastapi import APIRouter
from backend.app.core.security import create_access_token
from backend.app.schemas.auth import RegisterRequest, TokenResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def token(payload: RegisterRequest) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(payload.email))

