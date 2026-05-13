#!/bin/bash
echo "=== 修复sys_user双重编码 ==="

mysql -u root -p200575 environment_hub << 'EOF'
-- Step 1: Convert columns to BLOB to strip charset interpretation
ALTER TABLE sys_user MODIFY real_name MEDIUMBLOB;
ALTER TABLE sys_user MODIFY real_name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE sys_user MODIFY department MEDIUMBLOB;
ALTER TABLE sys_user MODIFY department VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE sys_user MODIFY email MEDIUMBLOB;
ALTER TABLE sys_user MODIFY email VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Verify
SELECT id, real_name, department FROM sys_user;
EOF

echo ""
echo "=== 修复data_source rows 1-3 ==="
mysql -u root -p200575 environment_hub << 'EOF'
ALTER TABLE data_source MODIFY source_name MEDIUMBLOB;
ALTER TABLE data_source MODIFY source_name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE data_source MODIFY description MEDIUMBLOB;
ALTER TABLE data_source MODIFY description VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

SELECT id, source_name FROM data_source;
EOF
