#!/bin/bash
echo "=== 1. MySQL连接编码测试 ==="
mysql -u root -p200575 --default-character-set=utf8mb4 environment_hub -e "SELECT id, real_name, department FROM sys_user; SELECT id, source_name FROM data_source WHERE id>=4;"

echo ""
echo "=== 2. 环境Hub最近错误 ==="
grep -E 'ERROR|Exception|AI|langchain|explanation|timeout|504|connect.*fail' /root/.pm2/logs/environment-hub-out.log 2>/dev/null | tail -15

echo ""
echo "=== 3. Python后端状态 ==="
curl -s --max-time 5 http://localhost:5001/health
echo ""

echo ""
echo "=== 4. 检查PM2全部服务 ==="
pm2 list

echo ""
echo "=== 5. 检查端口 ==="
ss -tlnp | grep -E '8083|5001|8080|8081'

echo ""
echo "=== 6. DashScope API测试 ==="
curl -s --max-time 10 -X POST 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-0395559857e04d5c8d9a51812a17fb76' \
  -d '{"model":"qwen-plus","messages":[{"role":"user","content":"say hi"}],"max_tokens":10}' 2>&1 | head -5
echo ""

echo ""
echo "=== 7. 已存储的风险分析数据 ==="
mysql -u root -p200575 --default-character-set=utf8mb4 environment_hub -e "SELECT id, city, risk_level, risk_score, key_factor, LEFT(explanation,80) as explanation_preview, create_time FROM risk_analysis_record ORDER BY id DESC LIMIT 3;"

echo ""
echo "=== 8. AQI数据统计 ==="
mysql -u root -p200575 --default-character-set=utf8mb4 environment_hub -e "SELECT COUNT(*) as aqi_count FROM aqi_data; SELECT COUNT(*) as spider_count FROM spider_raw_data; SELECT COUNT(*) as fetch_count FROM data_fetch_record;"
