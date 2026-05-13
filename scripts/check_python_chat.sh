#!/bin/bash
echo "=== Python recent output ==="
cat /opt/environment-hub/logs/python-out.log | tail -20

echo ""
echo "=== Python recent error ==="
cat /opt/environment-hub/logs/python-err.log | tail -10

echo ""
echo "=== Test chat API directly ==="
curl -s --max-time 30 -X POST http://localhost:5001/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"请用一句话介绍宜春"}' | head -200
