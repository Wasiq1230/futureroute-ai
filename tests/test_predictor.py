from ai_engine.inference.predictor import MobilityPredictor


def test_predictor_returns_explainable_scores():
    predictor = MobilityPredictor(artifact_dir="missing-artifacts")
    result = predictor.predict_route(
        {
            "distance_km": 12.5,
            "duration_minutes": 24.0,
            "weather_risk": 0.2,
            "mean_congestion": 0.4,
            "incident_severity": 0.1,
            "priority": "balanced",
            "route_index": 1,
        }
    )
    assert 0 <= result["congestion_risk"] <= 1
    assert result["eta_minutes"] > 0
    assert result["fuel_liters"] > 0
    assert result["explanation"]

