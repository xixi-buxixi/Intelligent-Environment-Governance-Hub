#!/bin/bash
# Final comprehensive check

# Get token
TOKEN=$(curl -s -X POST http://localhost:8083/environment/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

echo "=== 1. 用户列表(验证编码修复) ==="
curl -s --max-time 10 "http://localhost:8083/environment/api/user/list?pageNum=1&pageSize=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if d.get('code')==200:
    for r in d['data'].get('records',d['data'].get('list',[])):
        print(f\"  {r.get('id')}: {r.get('realName','')} / {r.get('department','')} / {r.get('username','')}\")
else:
    print('ERROR:', d.get('message',''))
" 2>/dev/null

echo ""
echo "=== 2. 数据源列表(验证编码修复) ==="
curl -s --max-time 10 "http://localhost:8083/environment/api/data-source/list" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if d.get('code')==200:
    for r in d['data'].get('records',d['data'].get('list',[])):
        print(f\"  {r.get('id')}: {r.get('sourceName','')} - {r.get('description','') or r.get('sourceCode','')}\")
elif 'timestamp' in d:
    print('Endpoint not found (404), trying alternatives...')
else:
    print('Response:', json.dumps(d, ensure_ascii=False)[:300])
" 2>/dev/null

echo ""
echo "=== 3. 尝试常见数据源API路径 ==="
for path in "data-source/list" "datasource/list" "source/list" "data/source/list" "fetch/sources"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
    "http://localhost:8083/environment/api/$path" -H "Authorization: Bearer $TOKEN" 2>/dev/null)
  echo "  /$path => $CODE"
done

echo ""
echo "=== 4. 系统日志中的API映射 ==="
grep -oE 'Mapped.*\{.*\}' /root/.pm2/logs/environment-hub-out.log 2>/dev/null | head -20

echo ""
echo "=== 5. Nginx超时配置 ==="
grep -E 'proxy_read_timeout|proxy_connect_timeout|location /environment' /etc/nginx/sites-enabled/* 2>/dev/null || echo "Not on Tencent server"
