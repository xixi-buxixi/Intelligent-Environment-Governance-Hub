#!/bin/bash

echo "=== 反编译所有Controller查找API路径 ==="
cd /tmp
for cls in $(jar tf /opt/environment-hub/environment-hub.jar | grep 'controller.*\.class$'); do
    jar xf /opt/environment-hub/environment-hub.jar "$cls" 2>/dev/null
    echo "--- $(basename $cls) ---"
    javap -p "$cls" 2>/dev/null | grep -E 'public|private|protected' | head -20
    strings "$cls" 2>/dev/null | grep -E 'GetMapping|PostMapping|RequestMapping|PutMapping|DeleteMapping' | head -10
    echo ""
done

echo ""
echo "=== 测试API端点 ==="
TOKEN=$(curl -s -X POST http://localhost:8083/environment/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

echo "Token obtained"

for path in "user/list" "user/page" "users" "sysuser/list" "system/user/list" \
            "data/source/list" "datasource/list" "source/list" \
            "fetch/list" "fetch/records" "fetch/sources"; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
        "http://localhost:8083/environment/api/$path" -H "Authorization: Bearer $TOKEN" 2>/dev/null)
    [ "$CODE" != "404" ] && echo "  /$path => $CODE"
done
