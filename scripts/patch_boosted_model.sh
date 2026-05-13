#!/bin/bash
# Add data availability check to run_feature to prevent hanging on empty data

TARGET="/opt/environment-hub/python-backend/src/services/boosted_air_model.py"
cp "$TARGET" "${TARGET}.bak"

python3 << 'PYEOF'
path = "/opt/environment-hub/python-backend/src/services/boosted_air_model.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add data check at the beginning of run_feature
old_code = '''def run_feature(feature: str) -> float:
    if is_fresh(feature):
        result = load_boosted_model(feature)
        write_result(result)
        print(f"Using fresh boosted model. Accuracy: {result.accuracy:.2f}%")
        return result.accuracy

    previous = read_existing_metrics(feature)
    previous_accuracy = float(previous.get("accuracy", 0) or 0)
    result = train_boosted_model(feature)'''

new_code = '''def run_feature(feature: str) -> float:
    if is_fresh(feature):
        result = load_boosted_model(feature)
        write_result(result)
        print(f"Using fresh boosted model. Accuracy: {result.accuracy:.2f}%")
        return result.accuracy

    # Check if training data exists before attempting to train
    from sqlalchemy import create_engine, text
    from src.config import DatabaseConfig
    engine = create_engine(DatabaseConfig.get_database_uri())
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM aqi_data")).scalar()
    if count == 0:
        raise RuntimeError("aqi_data table is empty; cannot train model. Please import historical data first.")

    previous = read_existing_metrics(feature)
    previous_accuracy = float(previous.get("accuracy", 0) or 0)
    result = train_boosted_model(feature)'''

content = content.replace(old_code, new_code)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched boosted_air_model.py successfully")
PYEOF
