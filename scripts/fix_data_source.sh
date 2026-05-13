#!/bin/bash
echo "=== 修复被破坏的 data_source rows 4-6 ==="

mysql -u root -p200575 --default-character-set=utf8mb4 environment_hub << 'EOF'
UPDATE data_source SET 
  source_name = '空气质量历史数据（天气后报）',
  description = '历史空气质量数据查询及下载平台',
  source_url = 'https://www.tianqihoubao.com'
WHERE id = 4;

UPDATE data_source SET 
  source_name = '历史气象数据',
  description = '历史气象数据查询及下载平台',
  source_url = 'https://www.tianqihoubao.com'
WHERE id = 5;

UPDATE data_source SET 
  source_name = '生态环境新闻',
  description = '宜春市生态环境局官网新闻',
  source_url = 'http://sthjj.yichun.gov.cn/ycssthjj/'
WHERE id = 6;

-- 验证
SELECT id, source_name, description FROM data_source;
EOF
