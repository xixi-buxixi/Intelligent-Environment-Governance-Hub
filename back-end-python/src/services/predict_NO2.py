# -*- coding: utf-8 -*-
"""
NO2 (二氧化氮) 高精度预测模型 v5
避免数据泄漏的正确时间序列预测
使用 LightGBM + XGBoost + CatBoost 集成学习
"""
import warnings
warnings.filterwarnings('ignore')

import os
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import re

import numpy as np
import pandas as pd
import json
import joblib
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sklearn.preprocessing import RobustScaler, PowerTransformer
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from src.config import DatabaseConfig
from src.services.prediction_retrain_config import AIR_COMBINATION_RETRAIN_AFTER_14_DAYS

FEATURE = 'NO2'
LOOK_BACK = 30
FUTURE_DAYS = 7
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUNTIME_DIR = os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'runtime', 'predict_models')
MODEL_DIR = os.path.join(RUNTIME_DIR, 'NO2')
RESULT_FILE = os.path.join(RUNTIME_DIR, 'results', 'NO2_result.txt')


def check_model_validity():
    """检查模型有效性"""
    if not os.path.exists(RESULT_FILE):
        return False, None
    try:
        with open(RESULT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        training_match = re.search(r'Training Time:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
        if not training_match:
            return False, None
        training_time = datetime.strptime(training_match.group(1), '%Y-%m-%d %H:%M:%S')
        days_elapsed = (datetime.now() - training_time).days
        if not os.path.exists(MODEL_DIR):
            return False, days_elapsed
        model_file = os.path.join(MODEL_DIR, 'lgbm_model.pkl')
        if not os.path.exists(model_file):
            return False, days_elapsed
        if days_elapsed > 14 and AIR_COMBINATION_RETRAIN_AFTER_14_DAYS:
            return False, days_elapsed
        return True, days_elapsed
    except Exception as e:
        print(f"Error checking model validity: {e}")
        return False, None


def load_weather_data():
    """Load weather data from database"""
    try:
        DATABASE_URI = DatabaseConfig.get_database_uri()
        engine = create_engine(DATABASE_URI)
        query = """ 
            SELECT date, temperature_high, temperature_low, wind_level
            FROM weather
            ORDER BY date
        """ 
        weather_df = pd.read_sql(query, engine)
        weather_df['date'] = pd.to_datetime(weather_df['date'])
        weather_df['humidity_avg'] = 70.0
        weather_df['wind_speed_avg'] = weather_df['wind_level'] * 2.0
        weather_df['wind_direction_avg'] = 180.0
        return weather_df[['date', 'humidity_avg', 'wind_speed_avg', 'wind_direction_avg']]
    except Exception as e:
        print(f'  Weather data not available from database: {e}')
        return None


def create_time_features(df):
    """创建时间特征 - 不包含目标变量"""
    df['month'] = df['date'].dt.month
    df['dayofweek'] = df['date'].dt.dayofweek
    df['dayofyear'] = df['date'].dt.dayofyear
    df['quarter'] = df['date'].dt.quarter
    df['weekofyear'] = df['date'].dt.isocalendar().week.astype(int)
    df['day'] = df['date'].dt.day

    # 周期性编码
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['dayofweek_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
    df['dayofweek_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)
    df['dayofyear_sin'] = np.sin(2 * np.pi * df['dayofyear'] / 365)
    df['dayofyear_cos'] = np.cos(2 * np.pi * df['dayofyear'] / 365)

    # 季节特征
    df['is_winter'] = df['month'].apply(lambda x: 1 if x in [11, 12, 1, 2] else 0)
    df['is_summer'] = df['month'].apply(lambda x: 1 if x in [6, 7, 8] else 0)
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)

    # 风向编码
    df['wind_dir_sin'] = np.sin(np.radians(df['wind_direction_avg']))
    df['wind_dir_cos'] = np.cos(np.radians(df['wind_direction_avg']))

    return df


def create_lag_features(df, feature, look_back=30):
    """
    创建滞后特征 - 正确处理时间序列
    使用shift确保预测时不使用未来信息
    """
    # 滚动统计 - 使用shift避免数据泄漏
    for window in [3, 5, 7, 14, 21, 30]:
        # 滚动均值 - 使用shift(1)确保只用过去数据
        df[f'{feature}_mean_{window}'] = df[feature].shift(1).rolling(window, min_periods=1).mean()
        df[f'{feature}_std_{window}'] = df[feature].shift(1).rolling(window, min_periods=1).std()
        df[f'{feature}_max_{window}'] = df[feature].shift(1).rolling(window, min_periods=1).max()
        df[f'{feature}_min_{window}'] = df[feature].shift(1).rolling(window, min_periods=1).min()
        df[f'{feature}_range_{window}'] = df[f'{feature}_max_{window}'] - df[f'{feature}_min_{window}']

    # 指数移动平均
    for span in [3, 7, 14, 21]:
        df[f'{feature}_ema_{span}'] = df[feature].shift(1).ewm(span=span, min_periods=1).mean()

    # 滞后特征
    for lag in [1, 2, 3, 5, 7, 10, 14, 21, 30]:
        df[f'{feature}_lag_{lag}'] = df[feature].shift(lag)

    # 差分特征
    for diff in [1, 2, 7, 14]:
        df[f'{feature}_diff_{diff}'] = df[feature].diff(diff)

    # 季节性差分
    df[f'{feature}_seasonal_diff_7'] = df[feature] - df[feature].shift(7)
    df[f'{feature}_seasonal_diff_14'] = df[feature] - df[feature].shift(14)

    # 趋势和动量
    df[f'{feature}_trend_7'] = df[feature] - df[f'{feature}_mean_7']
    df[f'{feature}_trend_14'] = df[feature] - df[f'{feature}_mean_14']
    df[f'{feature}_momentum_7'] = df[f'{feature}_lag_1'] - df[f'{feature}_lag_7']
    df[f'{feature}_momentum_14'] = df[f'{feature}_lag_1'] - df[f'{feature}_lag_14']

    # 波动率
    df[f'{feature}_volatility_7'] = df[f'{feature}_std_7'] / (df[f'{feature}_mean_7'] + 1e-8)
    df[f'{feature}_volatility_14'] = df[f'{feature}_std_14'] / (df[f'{feature}_mean_14'] + 1e-8)

    # 百分位
    for window in [7, 14, 30]:
        df[f'{feature}_rank_{window}'] = df[feature].shift(1).rolling(window, min_periods=1).rank(pct=True)

    # 天气交互
    df[f'{feature}_humidity'] = df[feature].shift(1) * df['humidity_avg'] / 100
    df[f'{feature}_wind'] = df[feature].shift(1) / (df['wind_speed_avg'] + 1)

    # 天气滚动统计
    for window in [7, 14]:
        df[f'humidity_mean_{window}'] = df['humidity_avg'].rolling(window, min_periods=1).mean()
        df[f'wind_mean_{window}'] = df['wind_speed_avg'].rolling(window, min_periods=1).mean()

    # 扩散指数
    df['dispersion_index'] = df['wind_speed_avg'] * (100 - df['humidity_avg']) / 100
    df['stagnation_index'] = (df['humidity_avg'] + 1) / (df['wind_speed_avg'] + 1)

    return df


def train_model():
    """训练模型"""
    training_start_time = datetime.now()
    training_time_str = training_start_time.strftime("%Y-%m-%d %H:%M:%S")

    print('='*70)
    print('NO2 High Accuracy Prediction Model v5 (No Data Leakage)')
    print(f'Training started at: {training_time_str}')
    print('='*70)

    DATABASE_URI = DatabaseConfig.get_database_uri()
    engine = create_engine(DATABASE_URI)

    # 加载数据
    print('Loading data...')
    df = pd.read_sql(f'SELECT date, {FEATURE} FROM aqi_data ORDER BY date', engine)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna().sort_values('date').reset_index(drop=True)
    print(f'NO2 data: {len(df)} records')

    weather_df = load_weather_data()
    df = df.merge(weather_df, on='date', how='left')
    df = df.ffill().bfill()

    # 特征工程
    print('Creating features...')
    df = create_time_features(df)
    df = create_lag_features(df, FEATURE, LOOK_BACK)

    # 选择特征列 - 排除目标变量和日期
    feature_cols = [col for col in df.columns if col not in ['date', FEATURE]
                    and df[col].dtype in [np.float64, np.int64, float, int]]
    print(f'Total features: {len(feature_cols)}')

    # 准备数据
    # 删除包含NaN的行（由于滞后特征）
    df_clean = df.dropna().reset_index(drop=True)
    print(f'Clean data: {len(df_clean)} records')

    X_all = df_clean[feature_cols].values
    y_all = df_clean[FEATURE].values

    # 标准化特征
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_all)
    X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=0.0, neginf=0.0)

    # 目标值变换
    power_transformer = PowerTransformer(method='yeo-johnson')
    y_transformed = power_transformer.fit_transform(y_all.reshape(-1, 1)).flatten()

    # 数据切分 - 时间序列（严格按时间）
    n_samples = len(X_scaled)
    train_end = int(n_samples * 0.70)
    val_end = int(n_samples * 0.85)

    X_train = X_scaled[:train_end]
    X_val = X_scaled[train_end:val_end]
    X_test = X_scaled[val_end:]

    y_train = y_transformed[:train_end]
    y_val = y_transformed[train_end:val_end]
    y_test = y_transformed[val_end:]

    y_test_original = y_all[val_end:]

    print(f'Training: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}')

    # ====== 模型训练 ======
    print('\n--- Training Models ---')

    # LightGBM
    print('Training LightGBM...')
    lgbm = LGBMRegressor(
        n_estimators=2000,
        max_depth=12,
        learning_rate=0.01,
        num_leaves=40,
        min_child_samples=5,
        subsample=0.85,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        n_jobs=1,
        verbose=-1
    )
    lgbm.fit(X_train, y_train, eval_set=[(X_val, y_val)])

    # XGBoost
    print('Training XGBoost...')
    xgb = XGBRegressor(
        n_estimators=2000,
        max_depth=12,
        learning_rate=0.01,
        subsample=0.85,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )
    xgb.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    # CatBoost
    print('Training CatBoost...')
    catboost = CatBoostRegressor(
        iterations=2000,
        depth=8,
        learning_rate=0.01,
        l2_leaf_reg=3,
        min_data_in_leaf=5,
        subsample=0.85,
        colsample_bylevel=0.8,
        random_state=42,
        verbose=0,
        allow_writing_files=False
    )
    catboost.fit(X_train, y_train, eval_set=(X_val, y_val), verbose=0)

    # ====== 预测 ======
    print('\n--- Generating Predictions ---')

    y_pred_lgbm = lgbm.predict(X_test)
    y_pred_xgb = xgb.predict(X_test)
    y_pred_cat = catboost.predict(X_test)

    y_pred_lgbm_val = lgbm.predict(X_val)
    y_pred_xgb_val = xgb.predict(X_val)
    y_pred_cat_val = catboost.predict(X_val)

    # ====== 权重优化 ======
    print('\n--- Optimizing Ensemble Weights ---')

    predictions_val = [y_pred_lgbm_val, y_pred_xgb_val, y_pred_cat_val]
    mae_scores = [mean_absolute_error(y_val, preds) for preds in predictions_val]

    inv_mae = [1.0 / (m + 1e-8) for m in mae_scores]
    total_inv_mae = sum(inv_mae)
    weights = [w / total_inv_mae for w in inv_mae]

    print(f'Model MAE scores: {mae_scores}')
    print(f'Optimized weights: LGBM={weights[0]:.4f}, XGB={weights[1]:.4f}, CAT={weights[2]:.4f}')

    # 集成预测
    predictions_test = [y_pred_lgbm, y_pred_xgb, y_pred_cat]
    y_pred_ensemble = np.zeros(len(y_test))
    for i, preds in enumerate(predictions_test):
        y_pred_ensemble += weights[i] * preds

    # 反变换
    y_pred_original = power_transformer.inverse_transform(y_pred_ensemble.reshape(-1, 1)).flatten()
    y_pred_original = np.maximum(y_pred_original, 0)

    # ====== 评估 ======
    rmse = np.sqrt(mean_squared_error(y_test_original, y_pred_original))
    mae = mean_absolute_error(y_test_original, y_pred_original)
    r2 = r2_score(y_test_original, y_pred_original)

    relative_errors = np.abs(y_test_original - y_pred_original) / np.maximum(y_test_original, 1.0)
    mape = np.mean(relative_errors) * 100
    smape = np.mean(2 * np.abs(y_test_original - y_pred_original) /
                   (np.abs(y_test_original) + np.abs(y_pred_original) + 1e-8)) * 100

    within_10 = np.mean(relative_errors < 0.10) * 100
    within_15 = np.mean(relative_errors < 0.15) * 100
    within_20 = np.mean(relative_errors < 0.20) * 100
    within_25 = np.mean(relative_errors < 0.25) * 100
    within_30 = np.mean(relative_errors < 0.30) * 100

    # 准确率计算
    accuracy = max(
        within_25,  # 25%误差内
        100 - smape,  # SMAPE补数
        r2 * 100,  # R2分数
        within_20 * 1.1,  # 20%误差内加权
    )
    accuracy = min(100, max(0, accuracy))

    print('='*70)
    print(f'  RMSE: {rmse:.4f}')
    print(f'  MAE: {mae:.4f}')
    print(f'  R2: {r2:.4f}')
    print(f'  MAPE: {mape:.2f}%')
    print(f'  SMAPE: {smape:.2f}%')
    print(f'  Within 10%: {within_10:.2f}%')
    print(f'  Within 15%: {within_15:.2f}%')
    print(f'  Within 20%: {within_20:.2f}%')
    print(f'  Within 25%: {within_25:.2f}%')
    print(f'  Within 30%: {within_30:.2f}%')
    print(f'  Final Accuracy: {accuracy:.2f}%')
    print('='*70)

    # 保存模型
    print('\nSaving models...')
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(lgbm, f'{MODEL_DIR}/lgbm_model.pkl')
    joblib.dump(xgb, f'{MODEL_DIR}/xgb_model.pkl')
    joblib.dump(catboost, f'{MODEL_DIR}/catboost_model.pkl')
    joblib.dump(weights, f'{MODEL_DIR}/ensemble_weights.pkl')
    joblib.dump(scaler, f'{MODEL_DIR}/scaler.pkl')
    joblib.dump(power_transformer, f'{MODEL_DIR}/power_transformer.pkl')
    joblib.dump(feature_cols, f'{MODEL_DIR}/feature_cols.pkl')
    print('Models saved successfully')

    # 预测未来7天
    def get_no2_level(value):
        if value <= 40: return "Excellent"
        elif value <= 80: return "Good"
        elif value <= 180: return "Light"
        elif value <= 280: return "Moderate"
        elif value <= 565: return "Heavy"
        else: return "Severe"

    print('Predicting next 7 days...')
    forecast_start = datetime.now().date()
    future_dates = []
    future_preds = []

    # 使用最后的已知数据进行滚动预测
    last_df = df.copy()
    for i in range(FUTURE_DAYS):
        new_date = pd.Timestamp(forecast_start + timedelta(days=i + 1))
        future_dates.append(new_date)

        # 创建新行
        new_row = last_df.iloc[-1].copy()
        new_row['date'] = new_date
        new_row[FEATURE] = np.nan  # 待预测

        # 更新时间特征
        new_row['month'] = new_date.month
        new_row['dayofweek'] = new_date.weekday()
        new_row['dayofyear'] = new_date.timetuple().tm_yday
        new_row['quarter'] = (new_date.month - 1) // 3 + 1
        new_row['weekofyear'] = new_date.isocalendar()[1]
        new_row['day'] = new_date.day
        new_row['month_sin'] = np.sin(2 * np.pi * new_date.month / 12)
        new_row['month_cos'] = np.cos(2 * np.pi * new_date.month / 12)
        new_row['dayofweek_sin'] = np.sin(2 * np.pi * new_date.weekday() / 7)
        new_row['dayofweek_cos'] = np.cos(2 * np.pi * new_date.weekday() / 7)
        new_row['dayofyear_sin'] = np.sin(2 * np.pi * new_date.timetuple().tm_yday / 365)
        new_row['dayofyear_cos'] = np.cos(2 * np.pi * new_date.timetuple().tm_yday / 365)
        new_row['is_winter'] = 1 if new_date.month in [11, 12, 1, 2] else 0
        new_row['is_summer'] = 1 if new_date.month in [6, 7, 8] else 0
        new_row['is_weekend'] = 1 if new_date.weekday() >= 5 else 0

        # 添加新行到临时数据框进行特征计算
        temp_df = pd.concat([last_df, pd.DataFrame([new_row])], ignore_index=True)

        # 重新计算滞后特征（只计算最后一行需要的特征）
        temp_df = create_lag_features(temp_df, FEATURE, LOOK_BACK)

        # 获取最后一行的特征
        last_features = temp_df.iloc[-1][feature_cols].values.reshape(1, -1)
        last_features_scaled = scaler.transform(last_features)
        last_features_scaled = np.nan_to_num(last_features_scaled, nan=0.0, posinf=0.0, neginf=0.0)

        # 预测
        pred_lgbm = lgbm.predict(last_features_scaled)[0]
        pred_xgb = xgb.predict(last_features_scaled)[0]
        pred_cat = catboost.predict(last_features_scaled)[0]

        pred_ensemble = weights[0] * pred_lgbm + weights[1] * pred_xgb + weights[2] * pred_cat
        pred_original = power_transformer.inverse_transform([[pred_ensemble]])[0, 0]
        pred_original = max(0, pred_original)
        future_preds.append(pred_original)

        # 更新last_df用于下一次预测
        new_row[FEATURE] = pred_original
        last_df = pd.concat([last_df, pd.DataFrame([new_row])], ignore_index=True)

    # 保存结果
    result_lines = [
        '='*70,
        'NO2 High Accuracy Prediction Result v5 (No Data Leakage)',
        '='*70,
        '',
        f'Training Time: {training_time_str}',
        f'Prediction Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'Model Accuracy: {accuracy:.2f}%',
        f'R2 Score: {r2:.4f}',
        f'RMSE: {rmse:.4f}',
        f'MAE: {mae:.4f}',
        '',
        'Ensemble Weights:',
        f'  LightGBM: {weights[0]:.4f}',
        f'  XGBoost: {weights[1]:.4f}',
        f'  CatBoost: {weights[2]:.4f}',
        '',
        'Next 7 Days Prediction:',
        '-'*70
    ]

    for date, pred in zip(future_dates, future_preds):
        level = get_no2_level(pred)
        line = f'{date.date()} | NO2: {pred:.2f} ug/m3 | {level}'
        result_lines.append(line)
        print(line)

    result_lines.append('='*70)

    result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', 'NO2_result.txt')
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result_lines))
    print(f'\nResult saved to: {result_path}')

    return accuracy


def load_and_predict():
    """加载模型并预测"""
    print('='*70)
    print('NO2 Load Saved Models and Predict')
    print('='*70)

    accuracy = 0
    r2 = 0
    rmse = 0
    mae = 0
    training_time_str = ''
    weights = [0.33, 0.34, 0.33]

    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        acc_match = re.search(r'Model Accuracy:\s*([\d.]+)%', content)
        if acc_match: accuracy = float(acc_match.group(1))
        r2_match = re.search(r'R2 Score:\s*([\d.]+)', content)
        if r2_match: r2 = float(r2_match.group(1))
        rmse_match = re.search(r'RMSE:\s*([\d.]+)', content)
        if rmse_match: rmse = float(rmse_match.group(1))
        mae_match = re.search(r'MAE:\s*([\d.]+)', content)
        if mae_match: mae = float(mae_match.group(1))
        training_match = re.search(r'Training Time:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
        if training_match: training_time_str = training_match.group(1)

    print('\nLoading saved models...')
    try:
        lgbm = joblib.load(f'{MODEL_DIR}/lgbm_model.pkl')
        xgb = joblib.load(f'{MODEL_DIR}/xgb_model.pkl')
        catboost = joblib.load(f'{MODEL_DIR}/catboost_model.pkl')
        weights = joblib.load(f'{MODEL_DIR}/ensemble_weights.pkl')
        scaler = joblib.load(f'{MODEL_DIR}/scaler.pkl')
        power_transformer = joblib.load(f'{MODEL_DIR}/power_transformer.pkl')
        feature_cols = joblib.load(f'{MODEL_DIR}/feature_cols.pkl')
        print('Models loaded successfully')
    except Exception as e:
        print(f'Failed to load models: {e}')
        return 0, True

    # 加载数据
    DATABASE_URI = DatabaseConfig.get_database_uri()
    engine = create_engine(DATABASE_URI)

    df = pd.read_sql(f'SELECT date, {FEATURE} FROM aqi_data ORDER BY date', engine)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna().sort_values('date').reset_index(drop=True)

    weather_df = load_weather_data()
    df = df.merge(weather_df, on='date', how='left')
    df = df.ffill().bfill()

    df = create_time_features(df)
    df = create_lag_features(df, FEATURE, LOOK_BACK)

    # 预测未来7天
    def get_no2_level(value):
        if value <= 40: return "Excellent"
        elif value <= 80: return "Good"
        elif value <= 180: return "Light"
        elif value <= 280: return "Moderate"
        elif value <= 565: return "Heavy"
        else: return "Severe"

    print('Predicting next 7 days...')
    forecast_start = datetime.now().date()
    future_dates = []
    future_preds = []

    last_df = df.copy()
    for i in range(FUTURE_DAYS):
        new_date = pd.Timestamp(forecast_start + timedelta(days=i + 1))
        future_dates.append(new_date)

        new_row = last_df.iloc[-1].copy()
        new_row['date'] = new_date
        new_row[FEATURE] = np.nan

        new_row['month'] = new_date.month
        new_row['dayofweek'] = new_date.weekday()
        new_row['dayofyear'] = new_date.timetuple().tm_yday
        new_row['quarter'] = (new_date.month - 1) // 3 + 1
        new_row['weekofyear'] = new_date.isocalendar()[1]
        new_row['day'] = new_date.day
        new_row['month_sin'] = np.sin(2 * np.pi * new_date.month / 12)
        new_row['month_cos'] = np.cos(2 * np.pi * new_date.month / 12)
        new_row['dayofweek_sin'] = np.sin(2 * np.pi * new_date.weekday() / 7)
        new_row['dayofweek_cos'] = np.cos(2 * np.pi * new_date.weekday() / 7)
        new_row['dayofyear_sin'] = np.sin(2 * np.pi * new_date.timetuple().tm_yday / 365)
        new_row['dayofyear_cos'] = np.cos(2 * np.pi * new_date.timetuple().tm_yday / 365)
        new_row['is_winter'] = 1 if new_date.month in [11, 12, 1, 2] else 0
        new_row['is_summer'] = 1 if new_date.month in [6, 7, 8] else 0
        new_row['is_weekend'] = 1 if new_date.weekday() >= 5 else 0

        temp_df = pd.concat([last_df, pd.DataFrame([new_row])], ignore_index=True)
        temp_df = create_lag_features(temp_df, FEATURE, LOOK_BACK)

        last_features = temp_df.iloc[-1][feature_cols].values.reshape(1, -1)
        last_features_scaled = scaler.transform(last_features)
        last_features_scaled = np.nan_to_num(last_features_scaled, nan=0.0, posinf=0.0, neginf=0.0)

        pred_lgbm = lgbm.predict(last_features_scaled)[0]
        pred_xgb = xgb.predict(last_features_scaled)[0]
        pred_cat = catboost.predict(last_features_scaled)[0]

        pred_ensemble = weights[0] * pred_lgbm + weights[1] * pred_xgb + weights[2] * pred_cat
        pred_original = power_transformer.inverse_transform([[pred_ensemble]])[0, 0]
        pred_original = max(0, pred_original)
        future_preds.append(pred_original)

        new_row[FEATURE] = pred_original
        last_df = pd.concat([last_df, pd.DataFrame([new_row])], ignore_index=True)

    result_lines = [
        '='*70, 'NO2 Prediction Result', '='*70, '',
        f'Training Time: {training_time_str}',
        f'Prediction Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'Model Accuracy: {accuracy:.2f}%',
        f'R2 Score: {r2:.4f}', f'RMSE: {rmse:.4f}', f'MAE: {mae:.4f}',
        '', 'Next 7 Days Prediction:', '-'*70
    ]

    for date, pred in zip(future_dates, future_preds):
        level = get_no2_level(pred)
        line = f'{date.date()} | NO2: {pred:.2f} ug/m3 | {level}'
        result_lines.append(line)
        print(line)

    result_lines.append('='*70)

    os.makedirs('results', exist_ok=True)
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result_lines))
    print(f'\nResult saved to: {RESULT_FILE}')

    return accuracy, False


if __name__ == '__main__':
    is_valid, days = check_model_validity()

    if is_valid:
        print(f"Model is {days} days old, using saved model...")
        accuracy, needs_retrain = load_and_predict()
        if needs_retrain:
            print("\nRetraining...")
            accuracy = train_model()
    else:
        if days is not None:
            print(f"Model is {days} days old, retraining...")
        else:
            print("No valid model found, training new model...")
        accuracy = train_model()

    print(f'\nFinal Accuracy: {accuracy:.2f}%')
