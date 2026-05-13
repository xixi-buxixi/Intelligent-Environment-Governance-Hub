#!/bin/bash
echo "=== Test DeepSeek API ==="
curl -s --max-time 10 -X POST 'https://api.deepseek.com/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-e51fa64310f5486aaf8b278f629cd7e5' \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"say hi"}],"max_tokens":10}'

echo ""
echo "=== Test AI Risk Analysis ==="
TOKEN=$(curl -s -X POST http://localhost:8083/environment/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")

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
    print('keyFactor:', data.get('keyFactor'))
    exp=data.get('explanation','') or ''
    print('explanation length:', len(exp))
    if exp:
        print('--- explanation (first 500) ---')
        print(exp[:500])
    else:
        print('explanation is EMPTY')
else:
    print('Error:', json.dumps(d,ensure_ascii=False)[:500])
"
