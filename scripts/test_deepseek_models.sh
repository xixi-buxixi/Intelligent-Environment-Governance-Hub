#!/bin/bash
echo "=== Test DeepSeek non-reasoning model ==="
curl -s --max-time 10 -X POST 'https://api.deepseek.com/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-e51fa64310f5486aaf8b278f629cd7e5' \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"say hi in 5 words"}],"max_tokens":20}'

echo ""
echo "=== Test with deepseek-v3 ==="
curl -s --max-time 10 -X POST 'https://api.deepseek.com/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-e51fa64310f5486aaf8b278f629cd7e5' \
  -d '{"model":"deepseek-v3","messages":[{"role":"user","content":"say hi in 5 words"}],"max_tokens":20}'
