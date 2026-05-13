#!/bin/bash
echo "=== Flask Routes ==="
cd /opt/environment-hub/python-backend && venv/bin/python3 -c "
from app import app
for rule in app.url_map.iter_rules():
    print(f'{rule.methods} {rule.rule}')
"

echo ""
echo "=== Test Chat API ==="
curl -s --max-time 10 -X POST http://localhost:5001/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"hello"}' | python3 -m json.tool 2>/dev/null | head -20

echo ""
echo "=== Test Predict API ==="
curl -s --max-time 120 -X POST http://localhost:5001/api/predict/air-quality \
  -H 'Content-Type: application/json' \
  -d '{"city":"宜春","factors":["AQI","PM25"],"horizonDays":3}' 2>&1 | python3 -m json.tool 2>/dev/null | head -40

echo ""
echo "=== Check predict function params ==="
grep -A30 'def predict_air_quality' /opt/environment-hub/python-backend/app.py
