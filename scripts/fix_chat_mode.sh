#!/bin/bash
# Fix Python backend: change default chat mode to 'direct' to avoid embedding API calls

TARGET="/opt/environment-hub/python-backend/app.py"

# Fix the default mode
sed -i 's/mode = data.get('\''mode'\'', '\''rag'\'')/mode = data.get('\''mode'\'', '\''direct'\'')/' "$TARGET"

echo "=== Verify change ==="
grep "mode = data.get" "$TARGET"

echo "=== Restart Python ==="
pm2 restart environment-python
sleep 12

echo "=== Health ==="
curl -s --max-time 10 http://localhost:5001/health

echo ""
echo "=== Test chat ==="
curl -s --max-time 30 -X POST http://localhost:5001/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"你好"}' | head -200
