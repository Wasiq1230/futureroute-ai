import hashlib
import math
import uuid
import httpx
from backend.app.core.config import get_settings
from backend.app.schemas.common import Coordinate
from backend.app.schemas.route import RouteCandidate, RouteRequest, RouteResponse, RouteScore, RouteStep
from backend.app.services.cache import cache
from backend.app.services.incidents import incident_service
from backend.app.services.traffic import traffic_service
from backend.app.services.weather import weather_service
from ai_engine.inference.predictor import MobilityPredictor


predictor = MobilityPredictor()


def _haversine_km(a: Coordinate, b: Coordinate) -> float:
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [a.lat, a.lon, b.lat, b.lon])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


class RoutingService:
    async def get_routes(self, payload: RouteRequest) -> RouteResponse:
        key = "route:" + hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
        cached = await cache.get_json(key)
        if cached:
            return RouteResponse(**cached)

        candidates = await self._ors_routes(payload)
        weather = await weather_service.current_risk(payload.destination.lat, payload.destination.lon)
        enriched = []
        for idx, route in enumerate(candidates):
            traffic_features = traffic_service.segment_features(route.geometry, payload.departure_time)
            incidents = incident_service.nearby_incidents(route.geometry)
            ml = predictor.predict_route(
                {
                    "distance_km": route.distance_km,
                    "duration_minutes": route.duration_minutes,
                    "weather_risk": weather["risk"],
                    "mean_congestion": sum(x["congestion_index"] for x in traffic_features) / max(1, len(traffic_features)),
                    "incident_severity": sum(x["severity"] for x in incidents),
                    "priority": payload.priority,
                    "route_index": idx,
                }
            )
            route.score = RouteScore(**ml)
            enriched.append(route)

        best = min(enriched, key=lambda item: item.score.ai_score)
        response = RouteResponse(
            request_id=str(uuid.uuid4()),
            best_route_id=best.id,
            routes=enriched,
            traffic_heatmap=traffic_service.heatmap([r.geometry for r in enriched], payload.departure_time),
            incidents=incident_service.nearby_incidents(best.geometry),
        )
        await cache.set_json(key, response.model_dump(), ttl=180)
        return response

    async def _ors_routes(self, payload: RouteRequest) -> list[RouteCandidate]:
        settings = get_settings()
        if not settings.ors_api_key:
            return self._fallback_routes(payload)
        body = {
            "coordinates": [
                [payload.source.lon, payload.source.lat],
                [payload.destination.lon, payload.destination.lat],
            ],
            "alternative_routes": {"target_count": 3, "share_factor": 0.7, "weight_factor": 1.6},
        }
        headers = {"Authorization": settings.ors_api_key}
        url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, json=body, headers=headers)
            response.raise_for_status()
        routes = []
        for idx, feature in enumerate(response.json()["features"][:3]):
            summary = feature["properties"]["summary"]
            coords = [Coordinate(lat=lat, lon=lon) for lon, lat in feature["geometry"]["coordinates"]]
            steps = []
            for segment in feature["properties"].get("segments", []):
                for step in segment.get("steps", [])[:12]:
                    steps.append(
                        RouteStep(
                            instruction=step.get("instruction", "Continue"),
                            distance_m=float(step.get("distance", 0)),
                            duration_s=float(step.get("duration", 0)),
                        )
                    )
            routes.append(
                RouteCandidate(
                    id=f"route-{idx+1}",
                    name=f"Route {chr(65 + idx)}",
                    geometry=coords,
                    distance_km=round(summary["distance"] / 1000, 2),
                    duration_minutes=round(summary["duration"] / 60, 1),
                    score=RouteScore(
                        ai_score=99,
                        eta_minutes=summary["duration"] / 60,
                        eta_confidence=0,
                        congestion_risk=0,
                        safety_risk=0,
                        weather_risk=0,
                        fuel_liters=0,
                        explanation=[],
                    ),
                    steps=steps,
                )
            )
        return routes

    def _fallback_routes(self, payload: RouteRequest) -> list[RouteCandidate]:
        base = _haversine_km(payload.source, payload.destination)
        routes = []
        offsets = [0, 0.012, -0.014]
        for idx, offset in enumerate(offsets):
            mid = Coordinate(
                lat=(payload.source.lat + payload.destination.lat) / 2 + offset,
                lon=(payload.source.lon + payload.destination.lon) / 2 - offset / 2,
            )
            geometry = [payload.source, mid, payload.destination]
            dist = base * (1 + abs(offset) * 5 + idx * 0.04)
            duration = dist / (42 - idx * 4) * 60
            routes.append(
                RouteCandidate(
                    id=f"route-{idx+1}",
                    name=f"Route {chr(65 + idx)}",
                    geometry=geometry,
                    distance_km=round(dist, 2),
                    duration_minutes=round(duration, 1),
                    score=RouteScore(
                        ai_score=99,
                        eta_minutes=duration,
                        eta_confidence=0,
                        congestion_risk=0,
                        safety_risk=0,
                        weather_risk=0,
                        fuel_liters=0,
                        explanation=[],
                    ),
                    steps=[
                        RouteStep(instruction="Head toward optimized corridor", distance_m=dist * 400, duration_s=duration * 20),
                        RouteStep(instruction="Continue on recommended arterial", distance_m=dist * 450, duration_s=duration * 24),
                        RouteStep(instruction="Arrive at destination", distance_m=dist * 150, duration_s=duration * 16),
                    ],
                )
            )
        return routes


routing_service = RoutingService()

