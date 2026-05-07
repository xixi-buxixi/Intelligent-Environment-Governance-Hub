import datetime as dt
import json
from typing import Dict, List, Optional

from spider.db import get_connection


def ensure_raw_table(conn):
    ddl = """
    CREATE TABLE IF NOT EXISTS spider_raw_data (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        source_code VARCHAR(100) NOT NULL,
        city VARCHAR(100) NOT NULL,
        data_date DATE,
        data_json JSON NOT NULL,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_spider_raw_source_city_date(source_code, city, data_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    with conn.cursor() as cursor:
        cursor.execute(ddl)


def _norm_date(raw) -> Optional[dt.date]:
    if raw is None:
        return None
    if isinstance(raw, dt.date):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    text = text.replace("年", "-").replace("月", "-").replace("日", "")
    text = text.split(" ")[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return dt.datetime.strptime(text, fmt).date()
        except Exception:
            continue
    return None


def save_raw_rows(source_code: str, city: str, rows: List[Dict], date_key: str = "date") -> int:
    if not rows:
        return 0

    conn = get_connection()
    inserted = 0
    try:
        ensure_raw_table(conn)
        sql = """
        INSERT INTO spider_raw_data(source_code, city, data_date, data_json)
        VALUES (%s, %s, %s, %s)
        """
        with conn.cursor() as cursor:
            for row in rows:
                data_date = _norm_date(row.get(date_key))
                payload = json.dumps(row, ensure_ascii=False)
                cursor.execute(sql, (source_code, city, data_date, payload))
                inserted += 1
        conn.commit()
        return inserted
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
