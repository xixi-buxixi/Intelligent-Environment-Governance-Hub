#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8083/environment/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")

echo "=== AI Risk Analysis with DeepSeek ==="
time curl -s --max-time 180 -X POST http://localhost:8083/environment/api/risk/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"city":"宜春","factors":["AQI","PM25","PM10","O3"],"horizonDays":7}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
if d.get('code')==200:
    data=d['data']
    print('riskLevel:', data.get('riskLevel'))
    print('riskScore:', data.get('riskScore'))
    exp=data.get('explanation','') or ''
    print('explanation length:', len(exp))
    if exp:
        print('--- explanation ---')
        print(exp[:1500])
    else:
        print('explanation is EMPTY')
else:
    print('Error:', json.dumps(d,ensure_ascii=False)[:500])
"
