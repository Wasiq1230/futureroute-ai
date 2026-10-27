import hashlib
import httpx
from backend.app.core.config import get_settings
from backend.app.services.cache import cache


class GeocodingService:
    async def search(self, query: str) -> list[dict]:
        normalized = query.strip()
        if len(normalized) < 2:
            return []
        key = "geocode:" + hashlib.sha256(normalized.lower().encode()).hexdigest()
        cached = await cache.get_json(key)
        if cached:
            return cached

        settings = get_settings()
        params = {
            "q": normalized,
            "format": "json",
            "limit": 8,
            "addressdetails": 1,
        }
        headers = {"User-Agent": "FutureRouteAI/2.0"}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(settings.nominatim_base_url, params=params, headers=headers)
            response.raise_for_status()
        results = [
            {
                "label": item.get("display_name", "Unknown"),
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "category": item.get("type", "place"),
            }
            for item in response.json()
        ]
        await cache.set_json(key, results, ttl=3600)
        return results


geocoding_service = GeocodingService()

