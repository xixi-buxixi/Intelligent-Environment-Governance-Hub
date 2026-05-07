# -*- coding: utf-8 -*-
"""Unified air quality prediction service using pre-trained ensemble models.

Loads pre-trained models for all 7 air factors and generates 7-day forecasts
without online training. Uses the same output format as the old predictor.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np

FACTOR_COLUMN_MAP = {
    "AQI": "AQI", "PM25": "PM25", "PM10": "PM10",
    "SO2": "SO2", "NO2": "NO2", "CO": "CO", "O3": "O3",
}

FLOAT_FACTORS = {"CO"}
HORIZON_DAYS = 7
RESULT_DIR = Path(__file__).resolve().parent.parent.parent / "runtime" / "predict_models" / "results"
RESULT_FACTOR_LABELS = {
    "AQI": "AQI",
    "PM25": "PM2.5",
    "PM10": "PM10",
    "SO2": "SO2",
    "NO2": "NO2",
    "CO": "CO",
    "O3": "O3",
}


@dataclass
class PredictValidationError(Exception):
    message: str
    status_code: int = 400


def normalize_factors(raw) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        values = [x.strip().upper() for x in raw.split(",") if x.strip()]
    elif isinstance(raw, list):
        values = [str(x).strip().upper() for x in raw if str(x).strip()]
    else:
        return []

    normalized: List[str] = []
    for one in values:
        if one == "PM2.5":
            one = "PM25"
        if one in FACTOR_COLUMN_MAP and one not in normalized:
            normalized.append(one)
    return normalized


# ---- per-factor loaders using the pre-trained bundles ----

def _read_result_values(factor: str) -> List[float]:
    path = RESULT_DIR / f"{factor}_result.txt"
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8", errors="replace")
    label = re.escape(RESULT_FACTOR_LABELS.get(factor, factor))
    matches = re.findall(
        rf"\d{{4}}-\d{{2}}-\d{{2}}\s*\|\s*{label}\s*:\s*([-+]?\d+(?:\.\d+)?)",
        content,
        flags=re.IGNORECASE,
    )
    return [max(0.0, float(value)) for value in matches[-HORIZON_DAYS:]]


def _predict_with_boosted(factor: str) -> tuple[List[float], Dict]:
    from src.services.boosted_air_model import is_fresh, load_boosted_model, run_feature, write_result
    needs_retrain = not is_fresh(factor)
    if needs_retrain:
        print(f"{factor} model expired or result is incomplete; retraining before prediction.")
        run_feature(factor)
    result = load_boosted_model(factor)
    write_result(result)
    return [max(0.0, float(v)) for v in result.future_values], {
        "factor": factor,
        "retrained": needs_retrain,
        "message": "模型已过期或结果缺失，已重新训练" if needs_retrain else "使用现有模型完成预测",
    }


def _predict_with_lightweight(factor: str) -> tuple[List[float], Dict]:
    from src.services.lightweight_air_model import saved_model_is_fresh, load_lightweight_model, run_feature, write_result
    needs_retrain = not saved_model_is_fresh(factor)
    if needs_retrain:
        print(f"{factor} model expired or result is incomplete; retraining before prediction.")
        run_feature(factor)
    result = load_lightweight_model(factor)
    write_result(result)
    return [max(0.0, float(v)) for v in result.future_values], {
        "factor": factor,
        "retrained": needs_retrain,
        "message": "模型已过期或结果缺失，已重新训练" if needs_retrain else "使用现有模型完成预测",
    }


def _predict_with_specialized(factor: str) -> tuple[List[float], Dict]:
    from src.services.specialized_low_air_model import saved_model_is_fresh, load_specialized_model, run_feature, write_result
    needs_retrain = not saved_model_is_fresh(factor)
    if needs_retrain:
        print(f"{factor} model expired or result is incomplete; retraining before prediction.")
        run_feature(factor)
    result = load_specialized_model(factor)
    write_result(result)
    return [max(0.0, float(v)) for v in result.future_values], {
        "factor": factor,
        "retrained": needs_retrain,
        "message": "模型已过期或结果缺失，已重新训练" if needs_retrain else "使用现有模型完成预测",
    }


def _predict_no2() -> tuple[List[float], Dict]:
    from src.services.predict_NO2 import check_model_validity, load_and_predict, train_model
    is_valid, days = check_model_validity()
    retrained = not is_valid
    if retrained:
        print(f"NO2 model expired or unavailable; retraining before prediction.")
        accuracy = train_model()
    else:
        accuracy, needs_retrain = load_and_predict()
        if needs_retrain:
            retrained = True
            accuracy = train_model()
    print(f"NO2 prediction accuracy: {accuracy:.2f}%")

    predictions = _read_result_values("NO2")
    return (predictions if len(predictions) == HORIZON_DAYS else [0.0] * HORIZON_DAYS), {
        "factor": "NO2",
        "retrained": retrained,
        "daysElapsed": days,
        "message": "模型已过期或结果缺失，已重新训练" if retrained else "使用现有模型完成预测",
    }


def _predict_o3() -> tuple[List[float], Dict]:
    from src.services.predict_O3 import check_model_validity, load_and_predict, train_model
    is_valid, days = check_model_validity()
    retrained = not is_valid
    if retrained:
        print(f"O3 model expired or unavailable; retraining before prediction.")
        accuracy = train_model()
    else:
        accuracy, needs_retrain = load_and_predict()
        if needs_retrain:
            retrained = True
            accuracy = train_model()
    print(f"O3 prediction accuracy: {accuracy:.2f}%")

    predictions = _read_result_values("O3")
    return (predictions if len(predictions) == HORIZON_DAYS else [0.0] * HORIZON_DAYS), {
        "factor": "O3",
        "retrained": retrained,
        "daysElapsed": days,
        "message": "模型已过期或结果缺失，已重新训练" if retrained else "使用现有模型完成预测",
    }


FACTOR_LOADER_MAP = {
    "AQI": lambda: _predict_with_boosted("AQI"),
    "PM10": lambda: _predict_with_boosted("PM10"),
    "CO": lambda: _predict_with_lightweight("CO"),
    "PM25": lambda: _predict_with_specialized("PM25"),
    "SO2": lambda: _predict_with_specialized("SO2"),
    "NO2": _predict_no2,
    "O3": _predict_o3,
}


class ComprehensivePredictor:
    """Unified prediction service using pre-trained ensemble models for all factors."""

    def predict(
        self,
        *,
        city: str,
        factors: List[str],
    ) -> Dict:
        city = str(city or "").strip()
        if not city:
            raise PredictValidationError("city 不能为空")

        factors = normalize_factors(factors)
        if not factors:
            raise PredictValidationError("factors 不能为空，且至少包含一个有效空气因子")

        predicted_by_factor: Dict[str, List[float]] = {}
        factor_statuses: List[Dict] = []
        for factor in factors:
            loader = FACTOR_LOADER_MAP.get(factor)
            if loader is None:
                raise PredictValidationError(f"不支持的预测因子: {factor}")
            try:
                values, status = loader()
                if len(values) != HORIZON_DAYS:
                    values = [0.0] * HORIZON_DAYS
                predicted_by_factor[factor] = values
                factor_statuses.append(status)
            except Exception as exc:
                raise PredictValidationError(
                    f"因子 {factor} 预测失败: {exc}", status_code=500
                ) from exc

        start_date = datetime.now().date() + timedelta(days=1)
        predictions: List[Dict] = []
        for day_idx in range(HORIZON_DAYS):
            one_day = {"date": (start_date + timedelta(days=day_idx)).isoformat()}
            for factor in factors:
                value = predicted_by_factor[factor][day_idx]
                if factor in FLOAT_FACTORS:
                    one_day[factor] = round(value, 2)
                else:
                    one_day[factor] = int(round(value))
            predictions.append(one_day)

        retrained_factors = [item["factor"] for item in factor_statuses if item.get("retrained")]
        return {
            "city": city,
            "factors": factors,
            "horizonDays": HORIZON_DAYS,
            "startDate": start_date.isoformat(),
            "historyDaysUsed": 365,
            "source": "model-prediction",
            "statusMessage": "模型已过期，已完成重新训练并生成预测结果" if retrained_factors else "已使用现有模型生成预测结果",
            "factorStatuses": factor_statuses,
            "retrainedFactors": retrained_factors,
            "expiredFactors": retrained_factors,
            "predictions": predictions,
        }


comprehensive_predictor = ComprehensivePredictor()
