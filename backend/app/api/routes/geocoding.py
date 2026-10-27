from fastapi import APIRouter, Query
from backend.app.services.geocoding import geocoding_service


router = APIRouter(prefix="/geocode", tags=["geocoding"])


@router.get("/search")
async def search_places(q: str = Query(min_length=2)) -> list[dict]:
    return await geocoding_service.search(q)

