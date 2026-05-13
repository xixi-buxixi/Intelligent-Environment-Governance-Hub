#!/bin/bash
# Test AI analysis on qiniuyun server

# Login and get token
RESP=$(curl -s -X POST http://localhost:8083/environment/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}')

TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

echo "=== Token obtained ==="

# Test overview
echo ""
echo "=== Risk Overview ==="
curl -s --max-time 30 http://localhost:8083/environment/api/risk/overview \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null | head -40

# Test AI analysis
echo ""
echo "=== AI Risk Analyze ==="
RESULT=$(curl -s --max-time 180 -X POST http://localhost:8083/environment/api/risk/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"city":"宜春","factors":["AQI","PM25","PM10","O3"],"horizonDays":7}')

echo "$RESULT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('code:', d.get('code'))
if d.get('code')==200:
    data=d['data']
    for k in ['riskLevel','riskScore','keyFactor','confidence']:
        print(f'{k}: {data.get(k)}')
    exp=data.get('explanation','')
    print('explanation length:', len(exp) if exp else 0)
    if exp and len(exp)>0:
        print('--- explanation ---')
        print(exp[:2000])
    else:
        print('explanation is EMPTY')
else:
    print('ERROR:', json.dumps(d,ensure_ascii=False)[:500])
"
