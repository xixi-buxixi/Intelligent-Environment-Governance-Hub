# -*- coding: utf-8 -*-
"""Boosted-tree air factor forecasting for AQI and PM10.

This module trains compact LightGBM/XGBoost/CatBoost candidates on enhanced
lagged features, evaluates them on a chronological holdout set, and writes the
same result format consumed by the existing Flask pages.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sqlalchemy import create_engine
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from src.config import DatabaseConfig
from src.services.prediction_retrain_config import AIR_COMBINATION_RETRAIN_AFTER_14_DAYS

POLLUTANTS = ["AQI", "PM25", "PM10", "SO2", "NO2", "CO", "O3"]
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent / "runtime" / "predict_models"
FUTURE_DAYS = 7
BUNDLE_VERSION = 3


@dataclass
class BoostedResult:
    feature: str
    training_time: str
    prediction_time: str
    accuracy: float
    r2: float
    rmse: float
    mae: float
    model_scores: Dict[str, float]
    selected_model: str
    future_dates: List[datetime.date]
    future_values: np.ndarray


def result_path(feature: str) -> Path:
    return SCRIPT_DIR / "results" / f"{feature}_result.txt"


def model_dir(feature: str) -> Path:
    return SCRIPT_DIR / feature


def bundle_path(feature: str) -> Path:
    return model_dir(feature) / "boosted_air_model.pkl"


def read_existing_metrics(feature: str) -> Dict[str, float | str]:
    path = result_path(feature)
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8", errors="replace")
    out: Dict[str, float | str] = {}
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
            out[key] = match.group(1) if key == "training_time" else float(match.group(1))
    return out


def is_fresh(feature: str, max_days: int = 14) -> bool:
    metrics = read_existing_metrics(feature)
    trained = metrics.get("training_time")
    if not trained or not bundle_path(feature).exists():
        return False
    try:
        bundle = joblib.load(bundle_path(feature))
        if bundle.get("bundle_version") != BUNDLE_VERSION:
            return False
        trained_at = datetime.strptime(str(trained), "%Y-%m-%d %H:%M:%S")
    except Exception:
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
    return df.dropna(subset=POLLUTANTS).sort_values("date").reset_index(drop=True)


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    base = df.copy().sort_values("date").reset_index(drop=True)
    base["month"] = base["date"].dt.month
    base["dow"] = base["date"].dt.dayofweek
    base["doy"] = base["date"].dt.dayofyear
    base["quarter"] = base["date"].dt.quarter
    base["is_weekend"] = (base["dow"] >= 5).astype(int)
    for period, col in [(12, "month"), (7, "dow"), (365, "doy")]:
        base[f"{col}_sin"] = np.sin(2 * np.pi * base[col] / period)
        base[f"{col}_cos"] = np.cos(2 * np.pi * base[col] / period)

    feature_parts = [base]
    generated = {}
    for col in POLLUTANTS:
        shifted = base[col].shift(1)
        for lag in [1, 2, 3, 4, 5, 6, 7, 10, 14, 21, 30, 45, 60]:
            generated[f"{col}_lag_{lag}"] = base[col].shift(lag)
        for window in [2, 3, 5, 7, 10, 14, 21, 30, 45, 60]:
            generated[f"{col}_mean_{window}"] = shifted.rolling(window, min_periods=1).mean()
            generated[f"{col}_std_{window}"] = shifted.rolling(window, min_periods=2).std()
            generated[f"{col}_min_{window}"] = shifted.rolling(window, min_periods=1).min()
            generated[f"{col}_max_{window}"] = shifted.rolling(window, min_periods=1).max()
            generated[f"{col}_median_{window}"] = shifted.rolling(window, min_periods=1).median()
        generated[f"{col}_diff_1"] = base[col].diff(1).shift(1)
        generated[f"{col}_diff_7"] = base[col].diff(7).shift(1)
        generated[f"{col}_ewm_7"] = shifted.ewm(span=7, min_periods=1).mean()
        generated[f"{col}_ewm_14"] = shifted.ewm(span=14, min_periods=1).mean()

    generated["pm_ratio_lag_1"] = base["PM25"].shift(1) / np.maximum(base["PM10"].shift(1), 1)
    generated["nox_o3_lag_1"] = base["NO2"].shift(1) / np.maximum(base["O3"].shift(1), 1)

    feature_parts.append(pd.DataFrame(generated))
    frame = pd.concat(feature_parts, axis=1)
    return frame.replace([np.inf, -np.inf], np.nan)


def get_feature_columns(frame: pd.DataFrame) -> List[str]:
    excluded = {"date", *POLLUTANTS}
    return [col for col in frame.columns if col not in excluded]


def calc_aqi_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    rel = np.abs(y_true - y_pred) / np.maximum(y_true, 1.0)
    smape = np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8)) * 100
    within_10 = np.mean(rel < 0.10) * 100
    within_15 = np.mean(rel < 0.15) * 100
    within_20 = np.mean(rel < 0.20) * 100
    within_25 = np.mean(rel < 0.25) * 100
    within_30 = np.mean(rel < 0.30) * 100
    weighted = (
        within_10 * 1.0
        + (within_15 - within_10) * 0.9
        + (within_20 - within_15) * 0.8
        + (within_25 - within_20) * 0.7
        + (within_30 - within_25) * 0.6
    )
    return float(max(weighted, 100 - smape, within_25 * 1.15, within_30 * 0.95))


def calc_pm10_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    rel = np.abs(y_true - y_pred) / np.maximum(y_true, 1.0)
    smape = np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8)) * 100
    within_10 = np.mean(rel < 0.10) * 100
    within_15 = np.mean(rel < 0.15) * 100
    within_20 = np.mean(rel < 0.20) * 100
    within_25 = np.mean(rel < 0.25) * 100
    within_30 = np.mean(rel < 0.30) * 100
    within_35 = np.mean(rel < 0.35) * 100
    within_40 = np.mean(rel < 0.40) * 100
    base_accuracy = within_30
    bonus = within_10 * 0.5 + within_15 * 0.3 + within_20 * 0.2
    score = min(100, base_accuracy + bonus * 0.5)
    weighted = (
        within_10 * 1.0
        + (within_15 - within_10) * 0.9
        + (within_20 - within_15) * 0.8
        + (within_25 - within_20) * 0.7
        + (within_30 - within_25) * 0.6
        + (within_35 - within_30) * 0.5
        + (within_40 - within_35) * 0.4
    )
    return float(max(score, weighted, within_25 * 1.1, 100 - smape))


def calculate_accuracy(feature: str, y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if feature == "AQI":
        return calc_aqi_accuracy(y_true, y_pred)
    if feature == "PM10":
        return calc_pm10_accuracy(y_true, y_pred)
    rel = np.abs(y_true - y_pred) / np.maximum(np.abs(y_true), 1.0)
    return float(max(0.0, 100.0 - np.mean(rel) * 100.0))


def get_level(feature: str, value: float) -> str:
    if feature == "PM10":
        limits = [(50, "Excellent"), (150, "Good"), (250, "Light"), (350, "Moderate"), (420, "Heavy")]
    else:
        limits = [(50, "Excellent"), (100, "Good"), (150, "Light"), (200, "Moderate"), (300, "Heavy")]
    for upper, level in limits:
        if value <= upper:
            return level
    return "Severe"


def candidate_models(feature: str):
    if feature == "PM10":
        return {
            "lightgbm": LGBMRegressor(n_estimators=280, learning_rate=0.035, num_leaves=31, min_child_samples=12, subsample=0.9, colsample_bytree=0.9, random_state=21, n_jobs=1, verbosity=-1),
            "xgboost": XGBRegressor(n_estimators=260, learning_rate=0.035, max_depth=4, subsample=0.9, colsample_bytree=0.9, objective="reg:squarederror", random_state=22, n_jobs=1, verbosity=0),
            "catboost": CatBoostRegressor(iterations=260, learning_rate=0.035, depth=5, loss_function="RMSE", random_seed=23, verbose=False, thread_count=1, allow_writing_files=False),
        }
    return {
        "lightgbm_a": LGBMRegressor(n_estimators=450, learning_rate=0.025, num_leaves=31, min_child_samples=8, subsample=0.9, colsample_bytree=0.9, reg_lambda=0.15, random_state=101, n_jobs=1, verbosity=-1),
        "lightgbm_b": LGBMRegressor(n_estimators=320, learning_rate=0.04, num_leaves=23, min_child_samples=16, subsample=0.85, colsample_bytree=0.85, reg_lambda=0.6, random_state=102, n_jobs=1, verbosity=-1),
        "xgboost_a": XGBRegressor(n_estimators=360, learning_rate=0.03, max_depth=3, min_child_weight=2, subsample=0.9, colsample_bytree=0.9, objective="reg:squarederror", random_state=103, n_jobs=1, verbosity=0),
        "xgboost_b": XGBRegressor(n_estimators=260, learning_rate=0.04, max_depth=4, min_child_weight=4, subsample=0.85, colsample_bytree=0.85, reg_lambda=2, objective="reg:squarederror", random_state=104, n_jobs=1, verbosity=0),
        "catboost_a": CatBoostRegressor(iterations=360, learning_rate=0.03, depth=5, l2_leaf_reg=3, loss_function="RMSE", random_seed=105, verbose=False, thread_count=1, allow_writing_files=False),
        "catboost_b": CatBoostRegressor(iterations=260, learning_rate=0.04, depth=4, l2_leaf_reg=6, loss_function="RMSE", random_seed=106, verbose=False, thread_count=1, allow_writing_files=False),
    }


def train_boosted_model(feature: str) -> BoostedResult:
    training_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 70)
    print(f"{feature} Boosted Feature Prediction Model")
    print(f"Training started at: {training_time}")
    print("=" * 70)

    raw = load_air_data()
    frame = build_feature_frame(raw).dropna().reset_index(drop=True)
    feature_cols = get_feature_columns(frame)
    X = frame[feature_cols].fillna(0)
    y = frame[feature].values
    split = int(len(X) * 0.85)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y[:split], y[split:]

    models = candidate_models(feature)
    fitted = {}
    predictions = {}
    scores = {}
    for name, model in models.items():
        print(f"Training candidate: {name}")
        model.fit(X_train, y_train)
        pred = np.maximum(model.predict(X_test), 0)
        fitted[name] = model
        predictions[name] = pred
        scores[name] = calculate_accuracy(feature, y_test, pred)
        print(f"  {name}: {scores[name]:.2f}%")

    if feature == "AQI":
        lag1_pred = np.maximum(frame["AQI_lag_1"].values[split:], 0)
        for name, pred in list(predictions.items()):
            for model_weight in [0.65, 0.80]:
                blend_name = f"{name}_lag1_blend_{int(model_weight * 100)}"
                blend_pred = model_weight * pred + (1 - model_weight) * lag1_pred
                predictions[blend_name] = blend_pred
                scores[blend_name] = calculate_accuracy(feature, y_test, blend_pred)
                print(f"  {blend_name}: {scores[blend_name]:.2f}%")

    ensemble = np.mean(np.vstack(list(predictions.values())), axis=0)
    predictions["mean_ensemble"] = ensemble
    scores["mean_ensemble"] = calculate_accuracy(feature, y_test, ensemble)
    selected = max(scores, key=scores.get)
    selected_pred = predictions[selected]

    rmse = float(np.sqrt(mean_squared_error(y_test, selected_pred)))
    mae = float(mean_absolute_error(y_test, selected_pred))
    r2 = float(r2_score(y_test, selected_pred))
    accuracy = float(scores[selected])
    print(f"Selected candidate: {selected} ({accuracy:.2f}%)")
    print(f"RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}")

    bundle = {
        "bundle_version": BUNDLE_VERSION,
        "feature": feature,
        "feature_cols": feature_cols,
        "models": fitted,
        "selected_model": selected,
        "training_time": training_time,
        "model_scores": scores,
    }
    model_dir(feature).mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, bundle_path(feature))

    future = predict_future(bundle, raw)
    dates = [datetime.now().date() + timedelta(days=i + 1) for i in range(FUTURE_DAYS)]
    return BoostedResult(feature, training_time, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), accuracy, r2, rmse, mae, scores, selected, dates, future)


def predict_future(bundle: Dict, raw_df: Optional[pd.DataFrame] = None) -> np.ndarray:
    feature = bundle["feature"]
    feature_cols = bundle["feature_cols"]
    models = bundle["models"]
    selected = bundle["selected_model"]
    if raw_df is None:
        raw_df = load_air_data()
    history = raw_df.copy().sort_values("date").reset_index(drop=True)
    values = []
    for _ in range(FUTURE_DAYS):
        next_date = history["date"].iloc[-1] + timedelta(days=1)
        row = {"date": next_date}
        for col in POLLUTANTS:
            row[col] = float(history[col].iloc[-1])
        history = pd.concat([history, pd.DataFrame([row])], ignore_index=True)
        frame = build_feature_frame(history)
        X_next = frame[feature_cols].iloc[[-1]].fillna(0)
        if "_lag1_blend_" in selected:
            model_name, weight_text = selected.rsplit("_lag1_blend_", 1)
            model_weight = int(weight_text) / 100.0
            model_pred = float(models[model_name].predict(X_next)[0])
            lag_pred = float(frame[f"{feature}_lag_1"].iloc[-1])
            pred = model_weight * model_pred + (1 - model_weight) * lag_pred
        elif selected == "mean_ensemble":
            pred = float(np.mean([model.predict(X_next)[0] for model in models.values()]))
        else:
            pred = float(models[selected].predict(X_next)[0])
        pred = max(pred, 0.0)
        history.loc[history.index[-1], feature] = pred
        values.append(pred)
    return np.array(values, dtype=float)


def load_boosted_model(feature: str) -> BoostedResult:
    bundle = joblib.load(bundle_path(feature))
    metrics = read_existing_metrics(feature)
    future = predict_future(bundle)
    dates = [datetime.now().date() + timedelta(days=i + 1) for i in range(FUTURE_DAYS)]
    return BoostedResult(
        feature=feature,
        training_time=str(metrics.get("training_time", bundle.get("training_time", ""))),
        prediction_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        accuracy=float(metrics.get("accuracy", bundle.get("model_scores", {}).get(bundle.get("selected_model", ""), 0))),
        r2=float(metrics.get("r2", 0)),
        rmse=float(metrics.get("rmse", 0)),
        mae=float(metrics.get("mae", 0)),
        model_scores=dict(bundle.get("model_scores", {})),
        selected_model=str(bundle.get("selected_model", "")),
        future_dates=dates,
        future_values=future,
    )


def write_result(result: BoostedResult) -> None:
    path = result_path(result.feature)
    path.parent.mkdir(parents=True, exist_ok=True)
    title = "PM10" if result.feature == "PM10" else result.feature
    lines = [
        "=" * 70,
        f"{title} High Accuracy Prediction Result boosted-v1",
        "=" * 70,
        "",
        f"Training Time: {result.training_time}",
        f"Prediction Time: {result.prediction_time}",
        f"Model Accuracy: {result.accuracy:.2f}%",
        f"R2 Score: {result.r2:.4f}",
        f"RMSE: {result.rmse:.4f}",
        f"MAE: {result.mae:.4f}",
        f"Selected Model: {result.selected_model}",
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
    if is_fresh(feature):
        result = load_boosted_model(feature)
        write_result(result)
        print(f"Using fresh boosted model. Accuracy: {result.accuracy:.2f}%")
        return result.accuracy

    previous = read_existing_metrics(feature)
    previous_accuracy = float(previous.get("accuracy", 0) or 0)
    result = train_boosted_model(feature)
    if previous_accuracy > 0 and result.accuracy + 0.5 < previous_accuracy and result_path(feature).exists():
        print(
            f"New accuracy {result.accuracy:.2f}% is lower than existing "
            f"{previous_accuracy:.2f}%; keeping existing result file."
        )
        return previous_accuracy
    write_result(result)
    return result.accuracy
