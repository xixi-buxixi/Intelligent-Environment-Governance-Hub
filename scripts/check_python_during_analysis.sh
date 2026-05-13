#!/bin/bash
echo "=== Clear Python logs ==="
> /opt/environment-hub/logs/python-out.log

echo "=== Trigger AI analysis ==="
TOKEN=$(curl -s -X POST http://localhost:8083/environment/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")

curl -s --max-time 120 -X POST http://localhost:8083/environment/api/risk/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"city":"宜春","factors":["AQI","PM25","PM10","O3"],"horizonDays":7}' > /dev/null 2>&1

echo "=== Python logs after analysis ==="
cat /opt/environment-hub/logs/python-out.log | tail -30

echo "=== Python error logs ==="
cat /opt/environment-hub/logs/python-err.log | tail -10
