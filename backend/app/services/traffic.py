from datetime import UTC, datetime
from math import sin, pi
from backend.app.schemas.common import Coordinate


class TrafficService:
    def segment_features(self, geometry: list[Coordinate], departure_time: datetime | None) -> list[dict]:
        now = departure_time or datetime.now(UTC)
        hour = now.hour + now.minute / 60
        rush = max(0, sin((hour - 7) / 3 * pi)) + max(0, sin((hour - 16) / 4 * pi))
        features = []
        for idx, point in enumerate(geometry[:: max(1, len(geometry) // 24)]):
            urban_density = min(1.0, 0.45 + abs(point.lat - 33.68) * 0.3 + abs(point.lon - 73.04) * 0.2)
            congestion = min(1.0, 0.22 + 0.32 * rush + 0.28 * urban_density + (idx % 5) * 0.025)
            features.append(
                {
                    "lat": point.lat,
                    "lon": point.lon,
                    "congestion_index": round(congestion, 3),
                    "speed_kph": round(58 - congestion * 34, 1),
                }
            )
        return features

    def heatmap(self, routes: list[list[Coordinate]], departure_time: datetime | None) -> list[tuple[float, float, float]]:
        points: list[tuple[float, float, float]] = []
        for geometry in routes:
            for item in self.segment_features(geometry, departure_time):
                points.append((item["lat"], item["lon"], item["congestion_index"]))
        return points


traffic_service = TrafficService()
