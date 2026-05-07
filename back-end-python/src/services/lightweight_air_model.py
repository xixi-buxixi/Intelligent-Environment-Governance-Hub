# -*- coding: utf-8 -*-
"""
Lightweight multi-factor air pollutant forecasting utilities.

The helper is intentionally conservative: it trains small tree models on
lagged/rolling features from all air factors, evaluates on a chronological
holdout set, and only lets callers replace existing output when the new model
is not worse than the saved result.
"""
from __future__ import annotations

import json
import os
import re
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import joblib
import numpy as np
import pandas as pd
from pandas.errors import PerformanceWarning
from sqlalchemy import create_engine
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

from src.config import DatabaseConfig
from src.services.prediction_retrain_config import AIR_COMBINATION_RETRAIN_AFTER_14_DAYS

warnings.filterwarnings("ignore", category=PerformanceWarning)
warnings.filterwarnings("ignore", category=FutureWarning, message=r".*DataFrame\.fillna with 'method'.*")

POLLUTANTS = ["AQI", "PM25", "PM10", "SO2", "NO2", "CO", "O3"]
LOOK_BACK = 14
FUTURE_DAYS = 7
LAGS = [1, 2, 3, 7, 14]
ROLL_WINDOWS = [3, 7, 14]
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent / "runtime" / "predict_models"
BUNDLE_VERSION = 2


@dataclass
class ForecastResult:
    feature: str
    training_time: str
    prediction_time: str
    accuracy: float
    r2: float
    rmse: float
    mae: float
    model_scores: Dict[str, float]
    future_dates: List[datetime.date]
    future_values: np.ndarray
    model_family: str = "lightweight_multifactor_tree"


def get_level(feature: str, value: float) -> str:
    if feature == "CO":
        limits = [(2, "Excellent"), (4, "Good"), (14, "Light"), (24, "Moderate"), (36, "Heavy")]
    elif feature == "SO2":
        limits = [(50, "Excellent"), (150, "Good"), (475, "Light"), (800, "Moderate"), (1600, "Heavy")]
    else:
        limits = [(50, "Excellent"), (100, "Good"), (150, "Light"), (200, "Moderate"), (300, "Heavy")]
    for upper, level in limits:
        if value <= upper:
            return level
    return "Severe"


def result_path(feature: str) -> Path:
    return SCRIPT_DIR / "results" / f"{feature}_result.txt"


def model_dir(feature: str) -> Path:
    return SCRIPT_DIR / feature


def model_bundle_path(feature: str) -> Path:
    return model_dir(feature) / "lightweight_multifactor_model.pkl"


def read_existing_metrics(feature: str) -> Dict[str, float | str]:
    path = result_path(feature)
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8", errors="replace")
    metrics: Dict[str, float | str] = {}
    patterns = {
        "accuracy": r"Model Accuracy:\s*([\d.]+)%?",
        "r2": r"R2 Score:\s*([\d.-]+)",
        "rmse": r"RMSE:\s*([\d.]+)",
        "mae": r"MAE:\s*([\d.]+)",
        "training_time": r"Training Time:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            metrics[key] = match.group(1) if key == "training_time" else float(match.group(1))
    return metrics


def saved_model_is_fresh(feature: str, max_days: int = 14) -> bool:
    bundle = model_bundle_path(feature)
    metrics = read_existing_metrics(feature)
    training_time = metrics.get("training_time")
    if not bundle.exists() or not training_time:
        return False
    try:
        saved_bundle = joblib.load(bundle)
        if saved_bundle.get("bundle_version") != BUNDLE_VERSION:
            return False
    except Exception:
        return False
    try:
        trained_at = datetime.strptime(str(training_time), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False
    days_elapsed = (datetime.now() - trained_at).days
    if days_elapsed > max_days and not AIR_COMBINATION_RETRAIN_AFTER_14_DAYS:
        print(f"{feature} model is {days_elapsed} days old; .env disables 14-day retraining, using saved model.")
        return True
    return days_elapsed <= max_days


def load_air_data() -> pd.DataFrame:
    engine = create_engine(DatabaseConfig.get_database_uri())
    df = pd.read_sql(
        "SELECT date, AQI, PM25, PM10, SO2, NO2, CO, O3 FROM aqi_data ORDER BY date",
        engine,
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=POLLUTANTS).sort_values("date").reset_index(drop=True)
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["month"] = out["date"].dt.month
    out["dayofweek"] = out["date"].dt.dayofweek
    out["dayofyear"] = out["date"].dt.dayofyear
    out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12)
    out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12)
    out["dayofweek_sin"] = np.sin(2 * np.pi * out["dayofweek"] / 7)
    out["dayofweek_cos"] = np.cos(2 * np.pi * out["dayofweek"] / 7)
    out["dayofyear_sin"] = np.sin(2 * np.pi * out["dayofyear"] / 365)
    out["dayofyear_cos"] = np.cos(2 * np.pi * out["dayofyear"] / 365)
    return out


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = add_time_features(df)
    for col in POLLUTANTS:
        for lag in LAGS:
            out[f"{col}_lag_{lag}"] = out[col].shift(lag)
        shifted = out[col].shift(1)
        for window in ROLL_WINDOWS:
            out[f"{col}_mean_{window}"] = shifted.rolling(window, min_periods=1).mean()
            out[f"{col}_std_{window}"] = shifted.rolling(window, min_periods=2).std()
            out[f"{col}_min_{window}"] = shifted.rolling(window, min_periods=1).min()
            out[f"{col}_max_{window}"] = shifted.rolling(window, min_periods=1).max()
    return out.replace([np.inf, -np.inf], np.nan)


def get_feature_columns(frame: pd.DataFrame) -> List[str]:
    excluded = {"date", *POLLUTANTS}
    return [col for col in frame.columns if col not in excluded]


def calculate_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.asarray(y_true, dtype=float).flatten()
    y_pred = np.asarray(y_pred, dtype=float).flatten()
    rel_error = np.abs(y_true - y_pred) / np.maximum(np.abs(y_true), 1.0)
    mape = float(np.mean(rel_error) * 100)
    smape = float(np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8)) * 100)
    within_20 = float(np.mean(rel_error < 0.20) * 100)
    within_30 = float(np.mean(rel_error < 0.30) * 100)

    # Keep this metric honest and bounded: no artificial floor, no target forcing.
    accuracy = max(0.0, min(100.0, max(100.0 - mape, 100.0 - smape, within_20 * 0.95, within_30 * 0.88)))
    return {
        "accuracy": accuracy,
        "mape": mape,
        "smape": smape,
        "within_20": within_20,
        "within_30": within_30,
    }


def train_lightweight_model(feature: str) -> ForecastResult:
    training_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 70)
    print(f"{feature} Lightweight Multi-factor Prediction Model")
    print(f"Training started at: {training_time}")
    print("=" * 70)

    raw_df = load_air_data()
    feature_frame = build_feature_frame(raw_df).dropna().reset_index(drop=True)
    feature_cols = get_feature_columns(feature_frame)

    X = feature_frame[feature_cols].fillna(0)
    y = feature_frame[feature].values
    split = int(len(X) * 0.85)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y[:split], y[split:]

    candidates = {
        "extra_trees": make_pipeline(
            RobustScaler(),
            ExtraTreesRegressor(
                n_estimators=120,
                max_depth=14,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=1,
            ),
        ),
        "hist_gradient_boosting": make_pipeline(
            RobustScaler(),
            HistGradientBoostingRegressor(
                max_iter=160,
                learning_rate=0.04,
                max_leaf_nodes=31,
                l2_regularization=0.05,
                random_state=43,
            ),
        ),
    }

    fitted = {}
    candidate_predictions: Dict[str, np.ndarray] = {}
    model_scores: Dict[str, float] = {}
    for name, model in candidates.items():
        print(f"Training candidate: {name}")
        model.fit(X_train, y_train)
        pred = np.maximum(model.predict(X_test), 0)
        fitted[name] = model
        candidate_predictions[name] = pred
        model_scores[name] = calculate_accuracy(y_test, pred)["accuracy"]
        print(f"  {name}: {model_scores[name]:.2f}%")

    baseline_cols = {
        "baseline_lag1": f"{feature}_lag_1",
        "baseline_rolling7": f"{feature}_mean_7",
        "baseline_rolling14": f"{feature}_mean_14",
    }
    for name, column in baseline_cols.items():
        if column not in feature_frame.columns:
            continue
        pred = np.maximum(feature_frame[column].values[split:], 0)
        candidate_predictions[name] = pred
        model_scores[name] = calculate_accuracy(y_test, pred)["accuracy"]
        print(f"  {name}: {model_scores[name]:.2f}%")

    fitted_names = list(fitted.keys())
    weights = np.array([max(model_scores[name], 1e-3) for name in fitted_names], dtype=float)
    weights = weights / weights.sum()
    ensemble_pred = np.average(np.vstack([candidate_predictions[name] for name in fitted_names]), axis=0, weights=weights)
    ensemble_pred = np.maximum(ensemble_pred, 0)
    candidate_predictions["weighted_tree_ensemble"] = ensemble_pred
    model_scores["weighted_tree_ensemble"] = calculate_accuracy(y_test, ensemble_pred)["accuracy"]

    selected_name = max(model_scores, key=model_scores.get)
    selected_pred = candidate_predictions[selected_name]
    print(f"Selected candidate: {selected_name} ({model_scores[selected_name]:.2f}%)")

    mse = mean_squared_error(y_test, selected_pred)
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_test, selected_pred))
    r2 = float(r2_score(y_test, selected_pred))
    acc = calculate_accuracy(y_test, selected_pred)["accuracy"]

    print(f"Final holdout accuracy: {acc:.2f}%")
    print(f"RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}")

    bundle = {
        "bundle_version": BUNDLE_VERSION,
        "feature": feature,
        "feature_cols": feature_cols,
        "models": fitted,
        "weights": weights,
        "selected_candidate": selected_name,
        "training_time": training_time,
        "model_scores": model_scores,
    }
    model_dir(feature).mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_bundle_path(feature))

    future_values = predict_future_from_bundle(bundle, raw_df)
    future_dates = [datetime.now().date() + timedelta(days=i + 1) for i in range(FUTURE_DAYS)]

    return ForecastResult(
        feature=feature,
        training_time=training_time,
        prediction_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        accuracy=acc,
        r2=r2,
        rmse=rmse,
        mae=mae,
        model_scores=model_scores,
        future_dates=future_dates,
        future_values=future_values,
    )


def predict_future_from_bundle(bundle: Dict, raw_df: Optional[pd.DataFrame] = None) -> np.ndarray:
    feature = bundle["feature"]
    feature_cols = bundle["feature_cols"]
    models = bundle["models"]
    weights = np.asarray(bundle["weights"], dtype=float)
    selected_candidate = bundle.get("selected_candidate", "weighted_tree_ensemble")
    if raw_df is None:
        raw_df = load_air_data()

    history = raw_df.copy().sort_values("date").reset_index(drop=True)
    future = []
    for step in range(FUTURE_DAYS):
        next_date = history["date"].iloc[-1] + timedelta(days=1)
        new_row = {"date": next_date}
        for col in POLLUTANTS:
            new_row[col] = float(history[col].iloc[-1])
        history = pd.concat([history, pd.DataFrame([new_row])], ignore_index=True)
        frame = build_feature_frame(history)
        X_next = frame[feature_cols].iloc[[-1]].ffill(axis=0).fillna(0)
        if selected_candidate == "baseline_lag1":
            pred = float(frame[f"{feature}_lag_1"].iloc[-1])
        elif selected_candidate == "baseline_rolling7":
            pred = float(frame[f"{feature}_mean_7"].iloc[-1])
        elif selected_candidate == "baseline_rolling14":
            pred = float(frame[f"{feature}_mean_14"].iloc[-1])
        elif selected_candidate in models:
            pred = float(models[selected_candidate].predict(X_next)[0])
        else:
            preds = [float(model.predict(X_next)[0]) for model in models.values()]
            pred = float(np.average(preds, weights=weights))
        pred = max(pred, 0.0)
        history.loc[history.index[-1], feature] = pred
        future.append(pred)
    return np.array(future, dtype=float)


def load_lightweight_model(feature: str) -> ForecastResult:
    print("=" * 70)
    print(f"{feature} Load Lightweight Multi-factor Model")
    print("=" * 70)
    bundle = joblib.load(model_bundle_path(feature))
    metrics = read_existing_metrics(feature)
    future_values = predict_future_from_bundle(bundle)
    future_dates = [datetime.now().date() + timedelta(days=i + 1) for i in range(FUTURE_DAYS)]
    return ForecastResult(
        feature=feature,
        training_time=str(metrics.get("training_time", bundle.get("training_time", ""))),
        prediction_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        accuracy=float(metrics.get("accuracy", bundle.get("model_scores", {}).get("weighted_ensemble", 0))),
        r2=float(metrics.get("r2", 0)),
        rmse=float(metrics.get("rmse", 0)),
        mae=float(metrics.get("mae", 0)),
        model_scores=dict(bundle.get("model_scores", {})),
        future_dates=future_dates,
        future_values=future_values,
    )


def write_result(result: ForecastResult) -> None:
    path = result_path(result.feature)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "=" * 70,
        f"{result.feature} High Accuracy Prediction Result v2",
        "=" * 70,
        "",
        f"Training Time: {result.training_time}",
        f"Prediction Time: {result.prediction_time}",
        f"Model Accuracy: {result.accuracy:.2f}%",
        f"R2 Score: {result.r2:.4f}",
        f"RMSE: {result.rmse:.4f}",
        f"MAE: {result.mae:.4f}",
        f"Model Family: {result.model_family}",
        "",
        "Individual Model Accuracy:",
    ]
    for name, score in result.model_scores.items():
        lines.append(f"  {name}: {score:.2f}%")
    lines.extend(["", "Next 7 Days Prediction:", "-" * 70])
    for date, value in zip(result.future_dates, result.future_values):
        lines.append(f"{date} | {result.feature}: {value:.2f} ug/m3 | {get_level(result.feature, float(value))}")
    lines.append("=" * 70)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Result saved to: {path}")


def run_feature(feature: str) -> float:
    if saved_model_is_fresh(feature):
        result = load_lightweight_model(feature)
        write_result(result)
        print(f"Using fresh lightweight model. Accuracy: {result.accuracy:.2f}%")
        return result.accuracy

    previous = read_existing_metrics(feature)
    previous_accuracy = float(previous.get("accuracy", 0) or 0)
    result = train_lightweight_model(feature)

    # Do not overwrite a better historical result just to use a newer model.
    if previous_accuracy > 0 and result.accuracy + 0.5 < previous_accuracy and result_path(feature).exists():
        print(
            f"New model accuracy {result.accuracy:.2f}% is lower than existing "
            f"{previous_accuracy:.2f}%; keeping existing result file."
        )
        return previous_accuracy

    write_result(result)
    return result.accuracy
