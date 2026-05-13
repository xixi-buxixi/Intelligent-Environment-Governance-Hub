#!/bin/bash
echo "=== 用 CONVERT 方法修复 sys_user 双重编码 ==="

mysql -u root -p200575 --default-character-set=utf8mb4 environment_hub << 'EOF'
-- 先查看当前数据状态
SELECT id, real_name, HEX(real_name) as hex_val, LENGTH(real_name) as byte_len, CHAR_LENGTH(real_name) as char_len FROM sys_user LIMIT 3;

-- 使用 CONVERT 修复双重编码
-- 原理: 当前存储的是 UTF-8 字节被当作 latin1 后再转成 utf8mb4 的结果
-- CONVERT(x USING latin1) 把 utf8mb4 字符串当作 latin1 解释，得到原始 UTF-8 字节
-- 然后 BINARY 保留原始字节，最后 CONVERT 回 utf8mb4 正确解读
UPDATE sys_user SET 
  real_name = CONVERT(BINARY(CONVERT(real_name USING latin1)) USING utf8mb4),
  department = CONVERT(BINARY(CONVERT(department USING latin1)) USING utf8mb4),
  email = CONVERT(BINARY(CONVERT(email USING latin1)) USING utf8mb4)
WHERE id > 0;

-- 验证
SELECT id, real_name, department, email FROM sys_user;
EOF

echo ""
echo "=== 用 CONVERT 方法修复 data_source 双重编码 ==="
mysql -u root -p200575 --default-character-set=utf8mb4 environment_hub << 'EOF'
SELECT id, source_name, HEX(source_name) as hex_val FROM data_source LIMIT 3;

UPDATE data_source SET 
  source_name = CONVERT(BINARY(CONVERT(source_name USING latin1)) USING utf8mb4),
  description = CONVERT(BINARY(CONVERT(description USING latin1)) USING utf8mb4)
WHERE id > 0;

SELECT id, source_name, description FROM data_source;
EOF
