import hashlib
import httpx
from backend.app.core.config import get_settings
from backend.app.services.cache import cache


class WeatherService:
    async def current_risk(self, lat: float, lon: float) -> dict:
        rounded = f"{lat:.3f}:{lon:.3f}"
        key = "weather:" + hashlib.sha256(rounded.encode()).hexdigest()
        cached = await cache.get_json(key)
        if cached:
            return cached

        settings = get_settings()
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation,rain,wind_speed_10m,visibility",
        }
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.get(settings.open_meteo_base_url, params=params)
                response.raise_for_status()
            current = response.json().get("current", {})
        except httpx.HTTPError:
            return {"risk": 0.18, "rain_mm": 0, "wind_kph": 0, "visibility_m": 10000}
        rain = float(current.get("rain") or current.get("precipitation") or 0)
        wind = float(current.get("wind_speed_10m") or 0)
        visibility = float(current.get("visibility") or 10000)
        risk = min(1.0, 0.18 + rain * 0.28 + max(0, wind - 20) * 0.015 + max(0, 3000 - visibility) / 8000)
        result = {"risk": round(risk, 3), "rain_mm": rain, "wind_kph": wind, "visibility_m": visibility}
        await cache.set_json(key, result, ttl=900)
        return result


weather_service = WeatherService()
