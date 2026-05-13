#!/bin/bash
echo "=== 修复sys_user双重编码 ==="

mysql -u root -p200575 --default-character-set=utf8mb4 environment_hub << 'EOF'
-- Fix double-encoded UTF-8: convert through latin1 then binary then back to utf8mb4
UPDATE sys_user SET real_name = CONVERT(BINARY(CONVERT(real_name USING latin1)) USING utf8mb4) WHERE id > 0;
UPDATE sys_user SET department = CONVERT(BINARY(CONVERT(department USING latin1)) USING utf8mb4) WHERE id > 0;
UPDATE sys_user SET email = CONVERT(BINARY(CONVERT(email USING latin1)) USING utf8mb4) WHERE id > 0;

-- Verify
SELECT id, real_name, department FROM sys_user;
EOF

echo ""
echo "=== 修复data_source剩余乱码行 ==="
mysql -u root -p200575 --default-character-set=utf8mb4 environment_hub << 'EOF'
-- Check which rows still have issues (rows 1-3 were fixed by ALTER TABLE already)
SELECT id, source_name, description FROM data_source;
EOF

echo ""
echo "=== 修复risk_analysis_record旧数据 ==="
mysql -u root -p200575 --default-character-set=utf8mb4 environment_hub << 'EOF'
UPDATE risk_analysis_record SET city = CONVERT(BINARY(CONVERT(city USING latin1)) USING utf8mb4) WHERE id = 1;
UPDATE risk_analysis_record SET trend_summary = CONVERT(BINARY(CONVERT(trend_summary USING latin1)) USING utf8mb4) WHERE id = 1;
UPDATE risk_analysis_record SET explanation = CONVERT(BINARY(CONVERT(explanation USING latin1)) USING utf8mb4) WHERE id = 1;

SELECT id, city, LEFT(explanation, 60) as explanation_preview FROM risk_analysis_record;
EOF
