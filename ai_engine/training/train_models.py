from __future__ import annotations

from pathlib import Path
import json
import joblib
import mlflow
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from ai_engine.data.synthetic import build_synthetic_mobility_dataset
from ai_engine.features.engineering import FEATURE_COLUMNS


TARGETS = ["eta_minutes", "congestion_risk", "safety_risk", "fuel_liters", "ai_score"]


def train(output_dir: str = "ai_engine/artifacts", dataset_path: str | None = None) -> dict:
    artifacts = Path(output_dir)
    artifacts.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(dataset_path) if dataset_path else build_synthetic_mobility_dataset()
    train_df, test_df = train_test_split(data, test_size=0.2, random_state=7)
    metrics: dict[str, dict] = {}

    mlflow.set_experiment("FutureRoute AI Mobility Models")
    with mlflow.start_run(run_name="route-ranking-suite"):
        for target in TARGETS:
            x_train = train_df[FEATURE_COLUMNS]
            y_train = train_df[target]
            x_test = test_df[FEATURE_COLUMNS]
            y_test = test_df[target]

            model = XGBRegressor(
                n_estimators=220,
                max_depth=4,
                learning_rate=0.045,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=7,
            )
            if target == "safety_risk":
                model = RandomForestRegressor(n_estimators=180, max_depth=9, random_state=7, n_jobs=-1)
            model.fit(x_train, y_train)
            pred = model.predict(x_test)
            target_metrics = {
                "mae": float(mean_absolute_error(y_test, pred)),
                "rmse": float(mean_squared_error(y_test, pred) ** 0.5),
                "r2": float(r2_score(y_test, pred)),
            }
            metrics[target] = target_metrics
            mlflow.log_metrics({f"{target}_{key}": value for key, value in target_metrics.items()})
            joblib.dump(model, artifacts / f"{target}.joblib")

    (artifacts / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(json.dumps(train(), indent=2))

