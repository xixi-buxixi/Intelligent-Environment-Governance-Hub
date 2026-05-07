# Spider 模块（当前项目）

本目录是 `Intelligent-Environment-Governance-Hub` 项目内置爬虫模块，和其他项目完全隔离。

## 已实现

- `aqi/aqi_history_spider.py`
  - 按城市与日期范围抓取历史 AQI 数据
  - 增量写入当前项目数据库 `environment_hub` 的 `aqi_data` 表
  - 采用 `INSERT ... ON DUPLICATE KEY UPDATE`，避免重复

## 运行方式

```bash
python spider/aqi/aqi_history_spider.py --city 宜春 --start-date 2026-04-01 --end-date 2026-04-19
```

## 数据库配置

通过环境变量读取：

- `DB_HOST`（默认 `localhost`）
- `DB_PORT`（默认 `3306`）
- `DB_USER`（默认 `root`）
- `DB_PASSWORD`（默认空）
- `DB_NAME`（默认 `environment_hub`）

