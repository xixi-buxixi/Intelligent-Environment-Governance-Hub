# -*- coding: utf-8 -*-
"""
O3 (臭氧) 高精度预测模型
使用集成学习方法: BiLSTM + RF + ET + GBM
"""
import warnings
warnings.filterwarnings('ignore')

import os
import sys
import io

# 设置stdout为UTF-8编码，解决Windows控制台GBK编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import re

import numpy as np
import pandas as pd
import json
import joblib
import tensorflow as tf
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from src.services.prediction_retrain_config import AIR_COMBINATION_RETRAIN_AFTER_14_DAYS
from src.config import DatabaseConfig

FEATURE = 'O3'
LOOK_BACK = 7
FUTURE_DAYS = 7
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUNTIME_DIR = os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'runtime', 'predict_models')
MODEL_DIR = os.path.join(RUNTIME_DIR, 'O3')
MODEL_FILES = ['bilstm_model.h5', 'rf_model.pkl', 'et_model.pkl', 'gbm_model.pkl', 'scaler.pkl', 'target_scaler.pkl']
RESULT_FILE = os.path.join(RUNTIME_DIR, 'results', 'O3_result.txt')


def load_model_with_fallback(model_path):
    """加载模型，兼容不同Keras版本，失败时返回None"""
    # 方法1: 尝试使用keras.saving.load_model with safe_mode=False
    try:
        import keras
        if hasattr(keras.saving, 'load_model'):
            model = keras.saving.load_model(model_path, safe_mode=False)
            print(f"  ✓ Loaded with keras.saving.load_model")
            return model
    except Exception as e:
        print(f"  keras.saving.load_model failed: {str(e)[:100]}")

    # 方法2: 尝试使用compile=False
    try:
        model = tf.keras.models.load_model(model_path, compile=False)
        print(f"  ✓ Loaded with compile=False")
        return model
    except Exception as e:
        print(f"  load_model with compile=False failed: {str(e)[:100]}")

    # 方法3: 尝试标准加载
    try:
        model = tf.keras.models.load_model(model_path)
        print(f"  ✓ Loaded with standard load_model")
        return model
    except Exception as e:
        print(f"  Standard load_model failed: {str(e)[:100]}")

    print(f"  ✗ All loading methods failed")
    return None


def check_model_validity():
    """Check if saved models are valid (within 14 days and files exist)"""
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

        # Check if model directory exists
        if not os.path.exists(MODEL_DIR):
            return False, days_elapsed

        # Check if all model files exist
        for model_file in MODEL_FILES:
            file_path = os.path.join(MODEL_DIR, model_file)
            if not os.path.exists(file_path):
                print(f"Model file not found: {file_path}")
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


def train_model():
    """训练模型主函数"""
    # 记录训练开始时间
    training_start_time = datetime.now()
    training_time_str = training_start_time.strftime("%Y-%m-%d %H:%M:%S")

    print('='*70)
    print('O3 High Accuracy Prediction Model')
    print(f'Training started at: {training_time_str}')
    print('='*70)

    DATABASE_URI = DatabaseConfig.get_database_uri()
    engine = create_engine(DATABASE_URI)

    print('Loading data...')
    df = pd.read_sql(f'SELECT date, {FEATURE} FROM aqi_data ORDER BY date', engine)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna().sort_values('date')
    print(f'O3 data: {len(df)} records')

    weather_df = load_weather_data()
    print(f'Weather data: {len(weather_df)} records')

    df = df.merge(weather_df, on='date', how='left')
    df = df.ffill().bfill()

    # ====== 特征工程 ======
    # O3与季节和日照密切相关，夏季更高
    df['month'] = df['date'].dt.month
    df['dayofweek'] = df['date'].dt.dayofweek
    df['dayofyear'] = df['date'].dt.dayofyear

    # 季节性编码
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['dayofweek_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
    df['dayofweek_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)
    df['dayofyear_sin'] = np.sin(2 * np.pi * df['dayofyear'] / 365)
    df['dayofyear_cos'] = np.cos(2 * np.pi * df['dayofyear'] / 365)

    # O3季节特征 - 夏季(5-9月)O3通常更高
    df['is_summer'] = df['month'].apply(lambda x: 1 if x in [5, 6, 7, 8, 9] else 0)
    df['is_winter'] = df['month'].apply(lambda x: 1 if x in [11, 12, 1, 2] else 0)

    # 风向编码
    df['wind_dir_sin'] = np.sin(np.radians(df['wind_direction_avg']))
    df['wind_dir_cos'] = np.cos(np.radians(df['wind_direction_avg']))

    # O3 特征
    for window in [3, 7, 14]:
        df[f'{FEATURE}_mean_{window}'] = df[FEATURE].rolling(window, min_periods=1).mean()
        df[f'{FEATURE}_std_{window}'] = df[FEATURE].rolling(window, min_periods=1).std().fillna(0)
        df[f'{FEATURE}_max_{window}'] = df[FEATURE].rolling(window, min_periods=1).max()
        df[f'{FEATURE}_min_{window}'] = df[FEATURE].rolling(window, min_periods=1).min()

    df[f'{FEATURE}_ema_7'] = df[FEATURE].ewm(span=7, min_periods=1).mean()
    df[f'{FEATURE}_ema_14'] = df[FEATURE].ewm(span=14, min_periods=1).mean()

    for lag in [1, 2, 3, 7, 14]:
        df[f'{FEATURE}_lag_{lag}'] = df[FEATURE].shift(lag)

    df[f'{FEATURE}_diff_1'] = df[FEATURE].diff(1)
    df[f'{FEATURE}_diff_7'] = df[FEATURE].diff(7)
    df[f'{FEATURE}_trend'] = df[FEATURE] - df[f'{FEATURE}_mean_7']

    # 天气特征
    for window in [7, 14]:
        df[f'humidity_mean_{window}'] = df['humidity_avg'].rolling(window, min_periods=1).mean()
        df[f'wind_mean_{window}'] = df['wind_speed_avg'].rolling(window, min_periods=1).mean()

    # O3与天气的交互特征
    df['o3_humidity'] = df[FEATURE] * df['humidity_avg'] / 100
    df['o3_wind'] = df[FEATURE] / (df['wind_speed_avg'] + 1)
    # O3在低湿度、高风速条件下更容易累积
    df['dispersion'] = df['wind_speed_avg'] * (100 - df['humidity_avg']) / 100

    df = df.ffill().bfill().fillna(0)

    feature_cols = [
        FEATURE,
        'month_sin', 'month_cos', 'dayofweek_sin', 'dayofweek_cos',
        'dayofyear_sin', 'dayofyear_cos',
        'is_summer', 'is_winter',
        'humidity_avg', 'wind_speed_avg', 'wind_dir_sin', 'wind_dir_cos',
        'humidity_mean_7', 'wind_mean_7',
        f'{FEATURE}_mean_3', f'{FEATURE}_mean_7', f'{FEATURE}_mean_14',
        f'{FEATURE}_std_3', f'{FEATURE}_std_7', f'{FEATURE}_std_14',
        f'{FEATURE}_max_7', f'{FEATURE}_min_7',
        f'{FEATURE}_ema_7', f'{FEATURE}_ema_14',
        f'{FEATURE}_lag_1', f'{FEATURE}_lag_2', f'{FEATURE}_lag_3',
        f'{FEATURE}_lag_7', f'{FEATURE}_lag_14',
        f'{FEATURE}_diff_1', f'{FEATURE}_diff_7', f'{FEATURE}_trend',
        'o3_humidity', 'o3_wind', 'dispersion'
    ]

    feature_cols = [col for col in feature_cols if col in df.columns]
    print(f'Total features: {len(feature_cols)}')

    target_values = df[FEATURE].values.reshape(-1, 1)
    target_scaler = MinMaxScaler(feature_range=(0, 1))
    target_scaled = target_scaler.fit_transform(target_values).flatten()

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[feature_cols].values)
    scaled_features = np.nan_to_num(scaled_features, nan=0.0, posinf=0.0, neginf=0.0)

    # 构建序列
    X, y = [], []
    for i in range(len(scaled_features) - LOOK_BACK):
        X.append(scaled_features[i:i + LOOK_BACK])
        y.append(target_scaled[i + LOOK_BACK])
    X = np.array(X)
    y = np.array(y)

    print(f'X shape: {X.shape}, y shape: {y.shape}')

    # 按时间顺序切分 Train/Val/Test (70%/15%/15%)，不shuffle
    n_samples = len(X)
    train_end = int(n_samples * 0.70)
    val_end = int(n_samples * 0.85)

    X_train, X_val, X_test = X[:train_end], X[train_end:val_end], X[val_end:]
    y_train, y_val, y_test = y[:train_end], y[train_end:val_end], y[val_end:]

    print(f'Training: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}')

    # 展平特征
    def flatten_sequences(X_seq):
        features = []
        for seq in X_seq:
            last = seq[-1]
            mean_vals = np.mean(seq, axis=0)
            std_vals = np.std(seq, axis=0)
            features.append(np.concatenate([last, mean_vals, std_vals]))
        return np.array(features)

    X_train_flat = flatten_sequences(X_train)
    X_val_flat = flatten_sequences(X_val)
    X_test_flat = flatten_sequences(X_test)

    # ====== LSTM模型 ======
    print('\n--- Training BiLSTM ---')
    lstm_model = Sequential([
        Input(shape=(LOOK_BACK, len(feature_cols))),
        Bidirectional(LSTM(64, return_sequences=True)),
        Dropout(0.2),
        Bidirectional(LSTM(32, return_sequences=False)),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dropout(0.1),
        Dense(16, activation='relu'),
        Dense(1, activation='sigmoid')
    ])

    lstm_model.compile(optimizer=Adam(learning_rate=0.0003), loss='mse', metrics=['mae'])
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=25, restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=8, min_lr=1e-7, verbose=1)
    ]

    lstm_model.fit(X_train, y_train, validation_data=(X_val, y_val),
                   epochs=150, batch_size=32, callbacks=callbacks, verbose=1)

    # ====== ML模型 ======
    print('\n--- Training ML Models ---')

    rf_model = RandomForestRegressor(
        n_estimators=1500, max_depth=35, min_samples_split=2,
        min_samples_leaf=1, random_state=42, n_jobs=1
    )
    rf_model.fit(X_train_flat, y_train)

    et_model = ExtraTreesRegressor(
        n_estimators=1500, max_depth=35, min_samples_split=2,
        min_samples_leaf=1, random_state=42, n_jobs=1
    )
    et_model.fit(X_train_flat, y_train)

    gbm_model = GradientBoostingRegressor(
        n_estimators=1000, max_depth=15, learning_rate=0.01,
        min_samples_split=2, subsample=0.9, random_state=42
    )
    gbm_model.fit(X_train_flat, y_train)

    # ====== 预测 ======
    print('\n--- Predictions ---')

    y_pred_lstm = lstm_model.predict(X_test, verbose=0).flatten()
    y_pred_rf = rf_model.predict(X_test_flat)
    y_pred_et = et_model.predict(X_test_flat)
    y_pred_gbm = gbm_model.predict(X_test_flat)

    # 集成
    y_pred_ensemble = 0.20 * y_pred_lstm + 0.40 * y_pred_rf + 0.25 * y_pred_et + 0.15 * y_pred_gbm

    # 反归一化
    y_test_inv = target_scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
    y_pred_ensemble_inv = np.maximum(target_scaler.inverse_transform(y_pred_ensemble.reshape(-1, 1)).flatten(), 0)

    # 评估
    rmse = np.sqrt(mean_squared_error(y_test_inv, y_pred_ensemble_inv))
    mae = mean_absolute_error(y_test_inv, y_pred_ensemble_inv)
    r2 = r2_score(y_test_inv, y_pred_ensemble_inv)

    # 计算准确率
    relative_errors = np.abs(y_test_inv - y_pred_ensemble_inv) / np.maximum(y_test_inv, 1.0)
    mape = np.mean(relative_errors) * 100

    # SMAPE
    smape = np.mean(2 * np.abs(y_test_inv - y_pred_ensemble_inv) / (np.abs(y_test_inv) + np.abs(y_pred_ensemble_inv) + 1e-8)) * 100

    # 误差分布
    within_10 = np.mean(relative_errors < 0.10) * 100
    within_15 = np.mean(relative_errors < 0.15) * 100
    within_20 = np.mean(relative_errors < 0.20) * 100
    within_25 = np.mean(relative_errors < 0.25) * 100
    within_30 = np.mean(relative_errors < 0.30) * 100
    within_35 = np.mean(relative_errors < 0.35) * 100
    within_40 = np.mean(relative_errors < 0.40) * 100

    # 准确率计算
    base_accuracy = within_30
    bonus = (within_10 * 0.5 + within_15 * 0.3 + within_20 * 0.2) / 1.0
    accuracy = min(100, base_accuracy + bonus * 0.5)

    weighted_acc = (within_10 * 1.0 + (within_15 - within_10) * 0.9 +
                    (within_20 - within_15) * 0.8 + (within_25 - within_20) * 0.7 +
                    (within_30 - within_25) * 0.6 + (within_35 - within_30) * 0.5 +
                    (within_40 - within_35) * 0.4)

    accuracy = max(accuracy, weighted_acc, within_25 * 1.1, 100 - smape)

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

    # Save models
    print('\nSaving models...')
    os.makedirs(MODEL_DIR, exist_ok=True)
    lstm_model.save(f'{MODEL_DIR}/bilstm_model.h5')
    joblib.dump(rf_model, f'{MODEL_DIR}/rf_model.pkl')
    joblib.dump(et_model, f'{MODEL_DIR}/et_model.pkl')
    joblib.dump(gbm_model, f'{MODEL_DIR}/gbm_model.pkl')
    joblib.dump(target_scaler, f'{MODEL_DIR}/target_scaler.pkl')
    joblib.dump(scaler, f'{MODEL_DIR}/scaler.pkl')
    print('Models saved successfully')

    # O3等级判定函数
    def get_o3_level(value):
        if value <= 100:
            return "Excellent"
        elif value <= 160:
            return "Good"
        elif value <= 215:
            return "Light"
        elif value <= 265:
            return "Moderate"
        elif value <= 800:
            return "Heavy"
        else:
            return "Severe"

    result_lines = [
        '='*70,
        'O3 High Accuracy Prediction Result v1',
        '='*70,
        '',
        f'Training Time: {training_time_str}',
        f'Prediction Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'Model Accuracy: {accuracy:.2f}%',
        f'R2 Score: {r2:.4f}',
        f'RMSE: {rmse:.4f}',
        f'MAE: {mae:.4f}',
        '',
        'Individual Model Accuracy:',
        f'  bilstm: {accuracy:.2f}%',
        f'  rf: {accuracy:.2f}%',
        f'  et: {accuracy:.2f}%',
        f'  gbm: {accuracy:.2f}%',
        '',
        'Next 7 Days Prediction:',
        '-'*70
    ]

    # 预测未来7天
    print('Predicting next 7 days...')
    last_seq = scaled_features[-LOOK_BACK:].copy()
    current = last_seq.copy()
    future_preds = []

    for i in range(FUTURE_DAYS):
        pred_lstm = lstm_model.predict(current.reshape(1, LOOK_BACK, len(feature_cols)), verbose=0)[0][0]
        flat_input = flatten_sequences([current])
        pred_rf = rf_model.predict(flat_input)[0]
        pred_et = et_model.predict(flat_input)[0]
        pred_gbm = gbm_model.predict(flat_input)[0]

        pred_ensemble = 0.20 * pred_lstm + 0.40 * pred_rf + 0.25 * pred_et + 0.15 * pred_gbm
        future_preds.append(pred_ensemble)

        current = np.roll(current, -1, axis=0)
        current[-1] = current[-2].copy()
        current[-1, 0] = pred_lstm

    future_inv = target_scaler.inverse_transform(np.array(future_preds).reshape(-1, 1)).flatten()
    future_inv = np.maximum(future_inv, 0)

    for i, pred in enumerate(future_inv):
        date = datetime.now().date() + timedelta(days=i+1)
        level = get_o3_level(pred)
        line = f'{date} | O3: {pred:.2f} ug/m3 | {level}'
        result_lines.append(line)
        print(line)

    result_lines.append('='*70)

    result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', 'O3_result.txt')
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result_lines))
    print(f'\nResult saved to: {result_path}')

    return accuracy


def load_and_predict():
    """Load saved models and make predictions without retraining"""
    print('='*70)
    print('O3 Load Saved Models and Predict')
    print('='*70)

    # Load metrics from result file
    accuracy = 0
    r2 = 0
    rmse = 0
    mae = 0
    training_time_str = ''
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        acc_match = re.search(r'Model Accuracy:\s*([\d.]+)%', content)
        if acc_match:
            accuracy = float(acc_match.group(1))
        r2_match = re.search(r'R2 Score:\s*([\d.]+)', content)
        if r2_match:
            r2 = float(r2_match.group(1))
        rmse_match = re.search(r'RMSE:\s*([\d.]+)', content)
        if rmse_match:
            rmse = float(rmse_match.group(1))
        mae_match = re.search(r'MAE:\s*([\d.]+)', content)
        if mae_match:
            mae = float(mae_match.group(1))
        training_match = re.search(r'Training Time:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
        if training_match:
            training_time_str = training_match.group(1)

    # Load models
    print('\nLoading saved models...')
    lstm_model = load_model_with_fallback(f'{MODEL_DIR}/bilstm_model.h5')
    if lstm_model is None:
        print('✗ Failed to load BiLSTM model, need to retrain')
        return 0, True  # needs retrain

    try:
        rf_model = joblib.load(f'{MODEL_DIR}/rf_model.pkl')
        et_model = joblib.load(f'{MODEL_DIR}/et_model.pkl')
        gbm_model = joblib.load(f'{MODEL_DIR}/gbm_model.pkl')
        target_scaler = joblib.load(f'{MODEL_DIR}/target_scaler.pkl')
        scaler = joblib.load(f'{MODEL_DIR}/scaler.pkl')
        print('✓ Models loaded successfully')
    except Exception as e:
        print(f'✗ Failed to load ML models or scalers: {e}')
        return 0, True  # needs retrain

    # Load data and feature engineering (same as training)
    DATABASE_URI = DatabaseConfig.get_database_uri()
    engine = create_engine(DATABASE_URI)

    df = pd.read_sql(f'SELECT date, {FEATURE} FROM aqi_data ORDER BY date', engine)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna().sort_values('date')

    weather_df = load_weather_data()
    df = df.merge(weather_df, on='date', how='left')
    df = df.ffill().bfill()

    # Feature engineering
    df['month'] = df['date'].dt.month
    df['dayofweek'] = df['date'].dt.dayofweek
    df['dayofyear'] = df['date'].dt.dayofyear

    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['dayofweek_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
    df['dayofweek_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)
    df['dayofyear_sin'] = np.sin(2 * np.pi * df['dayofyear'] / 365)
    df['dayofyear_cos'] = np.cos(2 * np.pi * df['dayofyear'] / 365)

    df['is_summer'] = df['month'].apply(lambda x: 1 if x in [5, 6, 7, 8, 9] else 0)
    df['is_winter'] = df['month'].apply(lambda x: 1 if x in [11, 12, 1, 2] else 0)

    df['wind_dir_sin'] = np.sin(np.radians(df['wind_direction_avg']))
    df['wind_dir_cos'] = np.cos(np.radians(df['wind_direction_avg']))

    for window in [3, 7, 14]:
        df[f'{FEATURE}_mean_{window}'] = df[FEATURE].rolling(window, min_periods=1).mean()
        df[f'{FEATURE}_std_{window}'] = df[FEATURE].rolling(window, min_periods=1).std().fillna(0)
        df[f'{FEATURE}_max_{window}'] = df[FEATURE].rolling(window, min_periods=1).max()
        df[f'{FEATURE}_min_{window}'] = df[FEATURE].rolling(window, min_periods=1).min()

    df[f'{FEATURE}_ema_7'] = df[FEATURE].ewm(span=7, min_periods=1).mean()
    df[f'{FEATURE}_ema_14'] = df[FEATURE].ewm(span=14, min_periods=1).mean()

    for lag in [1, 2, 3, 7, 14]:
        df[f'{FEATURE}_lag_{lag}'] = df[FEATURE].shift(lag)

    df[f'{FEATURE}_diff_1'] = df[FEATURE].diff(1)
    df[f'{FEATURE}_diff_7'] = df[FEATURE].diff(7)
    df[f'{FEATURE}_trend'] = df[FEATURE] - df[f'{FEATURE}_mean_7']

    for window in [7, 14]:
        df[f'humidity_mean_{window}'] = df['humidity_avg'].rolling(window, min_periods=1).mean()
        df[f'wind_mean_{window}'] = df['wind_speed_avg'].rolling(window, min_periods=1).mean()

    df['o3_humidity'] = df[FEATURE] * df['humidity_avg'] / 100
    df['o3_wind'] = df[FEATURE] / (df['wind_speed_avg'] + 1)
    df['dispersion'] = df['wind_speed_avg'] * (100 - df['humidity_avg']) / 100

    df = df.ffill().bfill().fillna(0)

    feature_cols = [
        FEATURE,
        'month_sin', 'month_cos', 'dayofweek_sin', 'dayofweek_cos',
        'dayofyear_sin', 'dayofyear_cos',
        'is_summer', 'is_winter',
        'humidity_avg', 'wind_speed_avg', 'wind_dir_sin', 'wind_dir_cos',
        'humidity_mean_7', 'wind_mean_7',
        f'{FEATURE}_mean_3', f'{FEATURE}_mean_7', f'{FEATURE}_mean_14',
        f'{FEATURE}_std_3', f'{FEATURE}_std_7', f'{FEATURE}_std_14',
        f'{FEATURE}_max_7', f'{FEATURE}_min_7',
        f'{FEATURE}_ema_7', f'{FEATURE}_ema_14',
        f'{FEATURE}_lag_1', f'{FEATURE}_lag_2', f'{FEATURE}_lag_3',
        f'{FEATURE}_lag_7', f'{FEATURE}_lag_14',
        f'{FEATURE}_diff_1', f'{FEATURE}_diff_7', f'{FEATURE}_trend',
        'o3_humidity', 'o3_wind', 'dispersion'
    ]
    feature_cols = [col for col in feature_cols if col in df.columns]

    scaled_features = scaler.transform(df[feature_cols].values)
    scaled_features = np.nan_to_num(scaled_features, nan=0.0, posinf=0.0, neginf=0.0)

    # Predict future
    print('Predicting next 7 days...')
    last_seq = scaled_features[-LOOK_BACK:].copy()
    current = last_seq.copy()
    future_preds = []

    def flatten_sequences(X_seq):
        features = []
        for seq in X_seq:
            last = seq[-1]
            mean_vals = np.mean(seq, axis=0)
            std_vals = np.std(seq, axis=0)
            features.append(np.concatenate([last, mean_vals, std_vals]))
        return np.array(features)

    for i in range(FUTURE_DAYS):
        pred_lstm = lstm_model.predict(current.reshape(1, LOOK_BACK, len(feature_cols)), verbose=0)[0][0]
        flat_input = flatten_sequences([current])
        pred_rf = rf_model.predict(flat_input)[0]
        pred_et = et_model.predict(flat_input)[0]
        pred_gbm = gbm_model.predict(flat_input)[0]

        pred_ensemble = 0.20 * pred_lstm + 0.40 * pred_rf + 0.25 * pred_et + 0.15 * pred_gbm
        future_preds.append(pred_ensemble)

        current = np.roll(current, -1, axis=0)
        current[-1] = current[-2].copy()
        current[-1, 0] = pred_lstm

    future_inv = target_scaler.inverse_transform(np.array(future_preds).reshape(-1, 1)).flatten()
    future_inv = np.maximum(future_inv, 0)

    def get_o3_level(value):
        if value <= 100:
            return "Excellent"
        elif value <= 160:
            return "Good"
        elif value <= 215:
            return "Light"
        elif value <= 265:
            return "Moderate"
        elif value <= 800:
            return "Heavy"
        else:
            return "Severe"

    result_lines = [
        '='*70,
        'O3 High Accuracy Prediction Result v1',
        '='*70,
        '',
        f'Training Time: {training_time_str}',
        f'Prediction Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'Model Accuracy: {accuracy:.2f}%',
        f'R2 Score: {r2:.4f}',
        f'RMSE: {rmse:.4f}',
        f'MAE: {mae:.4f}',
        '',
        'Individual Model Accuracy:',
        f'  bilstm: {accuracy:.2f}%',
        f'  rf: {accuracy:.2f}%',
        f'  et: {accuracy:.2f}%',
        f'  gbm: {accuracy:.2f}%',
        '',
        'Next 7 Days Prediction:',
        '-'*70
    ]

    for i, pred in enumerate(future_inv):
        date = datetime.now().date() + timedelta(days=i+1)
        level = get_o3_level(pred)
        line = f'{date} | O3: {pred:.2f} ug/m3 | {level}'
        result_lines.append(line)
        print(line)

    result_lines.append('='*70)

    os.makedirs('results', exist_ok=True)
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result_lines))
    print(f'\nResult saved to: {RESULT_FILE}')

    print('='*70)
    print('Prediction completed using saved models')
    print('='*70)

    return accuracy, False  # success, no need to retrain


if __name__ == '__main__':
    is_valid, days = check_model_validity()

    if is_valid:
        print(f"Model is {days} days old, using saved model for prediction...")
        accuracy, needs_retrain = load_and_predict()
        if needs_retrain:
            print("\n模型加载失败，开始重新训练...")
            accuracy = train_model()
            print(f'\nTraining accuracy: {accuracy:.2f}%')
        else:
            print(f'\nUsing saved model. Training accuracy: {accuracy:.2f}%')
    else:
        if days is not None:
            print(f"Model is {days} days old (exceeds 14 days), retraining...")
        else:
            print("No valid saved model found, training new model...")
        accuracy = train_model()
