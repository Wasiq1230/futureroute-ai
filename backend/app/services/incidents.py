from backend.app.schemas.common import Coordinate


class IncidentService:
    def nearby_incidents(self, geometry: list[Coordinate]) -> list[dict]:
        if not geometry:
            return []
        mid = geometry[len(geometry) // 2]
        return [
            {
                "id": "synthetic-roadwork-1",
                "kind": "roadwork",
                "severity": 0.42,
                "lat": round(mid.lat + 0.003, 6),
                "lon": round(mid.lon - 0.002, 6),
                "source": "city_feed_simulator",
                "description": "Moderate construction impact detected from municipal feed simulator.",
            }
        ]


incident_service = IncidentService()

