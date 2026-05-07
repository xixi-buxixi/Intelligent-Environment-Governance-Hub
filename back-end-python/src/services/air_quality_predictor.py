from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FACTOR_COLUMN_MAP = {
    "AQI": "AQI",
    "PM25": "PM25",
    "PM10": "PM10",
    "SO2": "SO2",
    "NO2": "NO2",
    "CO": "CO",
    "O3": "O3",
}

FLOAT_FACTORS = {"CO"}
MODEL_VALID_DAYS = 14
HORIZON_DAYS = 7
LOOK_BACK_DAYS = 14
MIN_HISTORY_POINTS = 30
MAX_HISTORY_DAYS = 365


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


class AirQualityPredictor:
    def __init__(self, model_root: str):
        self.model_root = model_root
        os.makedirs(self.model_root, exist_ok=True)

    def predict(
        self,
        *,
        city: str,
        factors: List[str],
        db_connection_factory,
    ) -> Dict:
        city = str(city or "").strip()
        if not city:
            raise PredictValidationError("city 不能为空")
        factors = normalize_factors(factors)
        if not factors:
            raise PredictValidationError("factors 不能为空，且至少包含一个有效空气因子")

        df = self._load_history_dataframe(city=city, factors=factors, db_connection_factory=db_connection_factory)
        if df.empty:
            raise PredictValidationError(f"城市 {city} 暂无可用历史数据")

        latest_date = pd.to_datetime(df["date"]).max().date()
        predicted_by_factor: Dict[str, List[float]] = {}

        for factor in factors:
            factor_series = self._extract_factor_series(df, factor)
            if len(factor_series) < MIN_HISTORY_POINTS:
                raise PredictValidationError(
                    f"因子 {factor} 历史样本不足（至少需要{MIN_HISTORY_POINTS}条，当前{len(factor_series)}条）"
                )
            predicted_by_factor[factor] = self._predict_factor(city=city, factor=factor, series=factor_series)

        start_date = latest_date + timedelta(days=1)
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

        history_days_used = int(
            min(MAX_HISTORY_DAYS, min(len(self._extract_factor_series(df, f)) for f in factors))
        )

        return {
            "city": city,
            "factors": factors,
            "horizonDays": HORIZON_DAYS,
            "startDate": start_date.isoformat(),
            "historyDaysUsed": history_days_used,
            "predictions": predictions,
        }

    def _load_history_dataframe(self, *, city: str, factors: List[str], db_connection_factory) -> pd.DataFrame:
        columns = [FACTOR_COLUMN_MAP[f] for f in factors]
        column_sql = ", ".join(["`date`"] + [f"`{c}`" for c in columns])
        not_null_sql = " OR ".join([f"`{c}` IS NOT NULL" for c in columns])
        sql = f"""
            SELECT {column_sql}
            FROM aqi_data
            WHERE city = %s
              AND ({not_null_sql})
            ORDER BY `date` DESC
            LIMIT {MAX_HISTORY_DAYS}
        """
        conn = None
        rows = []
        try:
            conn = db_connection_factory()
            with conn.cursor() as cursor:
                cursor.execute(sql, (city,))
                rows = cursor.fetchall()
        except Exception as exc:
            raise PredictValidationError(f"读取历史数据失败: {exc}", status_code=500) from exc
        finally:
            if conn is not None:
                conn.close()

        if not rows:
            return pd.DataFrame(columns=["date"] + factors)

        rows = list(reversed(rows))
        data = {"date": [], **{f: [] for f in factors}}
        for row in rows:
            data["date"].append(pd.to_datetime(row[0]))
            for idx, factor in enumerate(factors, start=1):
                try:
                    value = float(row[idx]) if row[idx] is not None else np.nan
                except Exception:
                    value = np.nan
                data[factor].append(value)

        df = pd.DataFrame(data)
        df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        return df

    def _extract_factor_series(self, df: pd.DataFrame, factor: str) -> pd.DataFrame:
        one = df[["date", factor]].copy()
        one = one.rename(columns={factor: "target"})
        one = one.dropna(subset=["target"]).sort_values("date").reset_index(drop=True)
        return one

    def _predict_factor(self, *, city: str, factor: str, series: pd.DataFrame) -> List[float]:
        artifact = self._load_valid_artifact(city=city, factor=factor)
        if artifact is None:
            artifact = self._train_and_store_artifact(city=city, factor=factor, series=series)

        predictions = self._recursive_forecast(series=series, artifact=artifact, days=HORIZON_DAYS)
        if len(predictions) != HORIZON_DAYS or any(np.isnan(v) for v in predictions):
            return self._fallback_predict(series["target"].tolist(), days=HORIZON_DAYS)
        return [max(0.0, float(v)) for v in predictions]

    def _artifact_paths(self, city: str, factor: str) -> Tuple[str, str]:
        city_hash = hashlib.md5(city.encode("utf-8")).hexdigest()[:12]
        folder = os.path.join(self.model_root, factor, city_hash)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "ensemble.joblib"), os.path.join(folder, "meta.json")

    def _load_valid_artifact(self, *, city: str, factor: str):
        model_path, meta_path = self._artifact_paths(city, factor)
        if not os.path.exists(model_path) or not os.path.exists(meta_path):
            return None
        try:
            with open(meta_path, "r", encoding="utf-8") as fp:
                meta = json.load(fp)
            trained_at = datetime.strptime(meta.get("trainedAt", ""), "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - trained_at).days > MODEL_VALID_DAYS:
                return None
            return load(model_path)
        except Exception:
            return None

    def _train_and_store_artifact(self, *, city: str, factor: str, series: pd.DataFrame):
        dataset = self._build_dataset(series)
        if len(dataset) < 20:
            return {"kind": "fallback"}

        feature_cols = [c for c in dataset.columns if c not in {"date", "target"}]
        X = dataset[feature_cols].values
        y = dataset["target"].values

        split_idx = max(int(len(dataset) * 0.8), len(dataset) - 14)
        split_idx = min(max(split_idx, 10), len(dataset) - 5)

        X_train, y_train = X[:split_idx], y[:split_idx]
        X_valid, y_valid = X[split_idx:], y[split_idx:]

        models = {
            "rf": RandomForestRegressor(n_estimators=220, random_state=42, min_samples_leaf=2),
            "et": ExtraTreesRegressor(n_estimators=260, random_state=42, min_samples_leaf=2),
            "gbm": GradientBoostingRegressor(random_state=42),
            "ridge": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("model", Ridge(alpha=1.0)),
                ]
            ),
        }

        valid_scores: Dict[str, float] = {}
        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                pred = model.predict(X_valid)
                mae = float(np.mean(np.abs(pred - y_valid)))
                valid_scores[name] = max(mae, 1e-6)
            except Exception:
                valid_scores[name] = 1e6

        score_sum = sum(1.0 / v for v in valid_scores.values())
        if score_sum <= 0:
            return {"kind": "fallback"}
        weights = {name: (1.0 / score) / score_sum for name, score in valid_scores.items()}

        artifact = {
            "kind": "ensemble",
            "featureCols": feature_cols,
            "models": models,
            "weights": weights,
        }

        model_path, meta_path = self._artifact_paths(city, factor)
        try:
            dump(artifact, model_path)
            with open(meta_path, "w", encoding="utf-8") as fp:
                json.dump(
                    {
                        "city": city,
                        "factor": factor,
                        "trainedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "modelValidDays": MODEL_VALID_DAYS,
                        "historySize": int(len(series)),
                    },
                    fp,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception:
            pass

        return artifact

    def _recursive_forecast(self, *, series: pd.DataFrame, artifact, days: int) -> List[float]:
        if artifact.get("kind") != "ensemble":
            return self._fallback_predict(series["target"].tolist(), days=days)

        work = series.copy().sort_values("date").reset_index(drop=True)
        out: List[float] = []
        for _ in range(days):
            next_date = pd.to_datetime(work["date"].iloc[-1]) + pd.Timedelta(days=1)
            row = self._build_single_feature_row(work["target"].tolist(), next_date)
            if row is None:
                return self._fallback_predict(series["target"].tolist(), days=days)

            x = np.array([row.get(c, 0.0) for c in artifact["featureCols"]], dtype=float).reshape(1, -1)
            pred_val = 0.0
            for name, model in artifact["models"].items():
                try:
                    pred_val += float(model.predict(x)[0]) * float(artifact["weights"].get(name, 0.0))
                except Exception:
                    continue

            last_val = float(work["target"].iloc[-1])
            cap = max(5.0, abs(last_val) * 0.35)
            pred_val = min(last_val + cap, max(last_val - cap, pred_val))
            pred_val = max(0.0, pred_val)

            out.append(pred_val)
            work.loc[len(work)] = [next_date, pred_val]

        return out

    def _fallback_predict(self, history_values: List[float], days: int) -> List[float]:
        if not history_values:
            return [0.0] * days
        series = pd.Series(history_values, dtype=float)
        base = float(series.tail(7).mean())
        trend = float((series.tail(14).diff().dropna().mean()) if len(series) >= 2 else 0.0)
        if np.isnan(trend):
            trend = 0.0

        out: List[float] = []
        for i in range(1, days + 1):
            val = base + trend * i
            if out:
                prev = out[-1]
            else:
                prev = history_values[-1]
            cap = max(5.0, abs(prev) * 0.35)
            val = min(prev + cap, max(prev - cap, val))
            out.append(max(0.0, float(val)))
        return out

    def _build_dataset(self, series: pd.DataFrame) -> pd.DataFrame:
        df = series.copy().sort_values("date").reset_index(drop=True)
        df["target"] = pd.to_numeric(df["target"], errors="coerce")
        df = df.dropna(subset=["target"])
        if df.empty:
            return pd.DataFrame()

        df["month"] = df["date"].dt.month
        df["dayofweek"] = df["date"].dt.dayofweek
        df["dayofyear"] = df["date"].dt.dayofyear
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12.0)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12.0)
        df["weekday_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7.0)
        df["weekday_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7.0)
        df["doy_sin"] = np.sin(2 * np.pi * df["dayofyear"] / 365.0)
        df["doy_cos"] = np.cos(2 * np.pi * df["dayofyear"] / 365.0)
        df["is_weekend"] = (df["dayofweek"] >= 5).astype(float)
        df["is_winter"] = df["month"].isin([11, 12, 1, 2]).astype(float)

        for lag in [1, 2, 3, 5, 7, 10, LOOK_BACK_DAYS]:
            df[f"lag_{lag}"] = df["target"].shift(lag)

        for w in [3, 5, 7, 10, LOOK_BACK_DAYS]:
            df[f"roll_mean_{w}"] = df["target"].rolling(w).mean()
            df[f"roll_std_{w}"] = df["target"].rolling(w).std()
            df[f"roll_max_{w}"] = df["target"].rolling(w).max()
            df[f"roll_min_{w}"] = df["target"].rolling(w).min()

        df["ema_7"] = df["target"].ewm(span=7).mean()
        df["ema_14"] = df["target"].ewm(span=14).mean()
        df["diff_1"] = df["target"].diff(1)
        df["diff_7"] = df["target"].diff(7)
        df["trend"] = df["target"] - df["roll_mean_7"]
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        return df

    def _build_single_feature_row(self, values: List[float], next_day: date | pd.Timestamp):
        if len(values) < LOOK_BACK_DAYS:
            return None
        series = pd.Series(values, dtype=float)
        next_day = pd.to_datetime(next_day)
        row = {
            "month_sin": float(np.sin(2 * np.pi * next_day.month / 12.0)),
            "month_cos": float(np.cos(2 * np.pi * next_day.month / 12.0)),
            "weekday_sin": float(np.sin(2 * np.pi * next_day.dayofweek / 7.0)),
            "weekday_cos": float(np.cos(2 * np.pi * next_day.dayofweek / 7.0)),
            "doy_sin": float(np.sin(2 * np.pi * next_day.dayofyear / 365.0)),
            "doy_cos": float(np.cos(2 * np.pi * next_day.dayofyear / 365.0)),
            "is_weekend": 1.0 if next_day.dayofweek >= 5 else 0.0,
            "is_winter": 1.0 if next_day.month in [11, 12, 1, 2] else 0.0,
        }
        for lag in [1, 2, 3, 5, 7, 10, LOOK_BACK_DAYS]:
            row[f"lag_{lag}"] = float(series.iloc[-lag])
        for w in [3, 5, 7, 10, LOOK_BACK_DAYS]:
            tail = series.tail(w)
            row[f"roll_mean_{w}"] = float(tail.mean())
            row[f"roll_std_{w}"] = float(tail.std() if len(tail) > 1 else 0.0)
            row[f"roll_max_{w}"] = float(tail.max())
            row[f"roll_min_{w}"] = float(tail.min())
        row["ema_7"] = float(series.ewm(span=7).mean().iloc[-1])
        row["ema_14"] = float(series.ewm(span=14).mean().iloc[-1])
        row["diff_1"] = float(series.iloc[-1] - series.iloc[-2])
        row["diff_7"] = float(series.iloc[-1] - series.iloc[-7])
        row["trend"] = float(series.iloc[-1] - series.tail(7).mean())
        return row
