#!/bin/bash
echo "=== Test DeepSeek non-reasoning model ==="
curl -s --max-time 10 -X POST 'https://api.deepseek.com/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer your_deepseek_api_key' \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"say hi in 5 words"}],"max_tokens":20}'

echo ""
echo "=== Test with deepseek-v3 ==="
curl -s --max-time 10 -X POST 'https://api.deepseek.com/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer your_deepseek_api_key' \
  -d '{"model":"deepseek-v3","messages":[{"role":"user","content":"say hi in 5 words"}],"max_tokens":20}'
