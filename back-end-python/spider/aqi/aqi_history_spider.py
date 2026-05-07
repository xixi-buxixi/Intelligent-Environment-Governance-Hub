import argparse
import datetime as dt
import re
import time
from typing import Callable, Dict, List, Tuple
import os
import subprocess

import requests

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "environment_hub")
MYSQL_CLI = os.getenv("MYSQL_CLI", "mysql")


CITY_PINYIN_MAP: Dict[str, str] = {
    "宜春": "jxyichun",
    "南昌": "jxnanchang",
    "九江": "jxjiujiang",
    "赣州": "jxganzhou",
    "吉安": "jxjian",
    "上饶": "jxshangrao",
    "抚州": "jxfuzhou",
    "景德镇": "jxjingdezhen",
    "萍乡": "jxpingxiang",
    "新余": "jxxinyu",
    "鹰潭": "jxyingtan",
}

BASE_URL = "https://www.tianqihoubao.com/aqi/{city_pinyin}-{yyyymm}.html"

SOURCE_STRATEGIES = {
    "aqi_history": {
        "url_template": BASE_URL,
        "sleep_sec": 0.30,
        "headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
        },
    },
    "aqi_history_ext": {
        "url_template": BASE_URL,
        "sleep_sec": 0.20,
        "headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.tianqihoubao.com/aqi/",
        },
    },
    "aqi_city_rank": {
        "url_template": BASE_URL,
        "sleep_sec": 0.25,
        "headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    },
    "aqi_realtime": {
        "url_template": BASE_URL,
        "sleep_sec": 0.15,
        "headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Cache-Control": "no-cache",
        },
    },
    "aqi_aggregated": {
        "url_template": BASE_URL,
        "sleep_sec": 0.18,
        "headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
        },
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description="AQI 历史数据爬虫（项目内置）")
    parser.add_argument("--city", required=True, help="城市名称，例如：宜春")
    parser.add_argument("--start-date", required=True, help="开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="结束日期，格式 YYYY-MM-DD")
    parser.add_argument("--source-code", default="aqi_history", help="数据源编码")
    return parser.parse_args()


def month_range(start_date: dt.date, end_date: dt.date) -> List[str]:
    cur = dt.date(start_date.year, start_date.month, 1)
    end = dt.date(end_date.year, end_date.month, 1)
    values = []
    while cur <= end:
        values.append(cur.strftime("%Y%m"))
        if cur.month == 12:
            cur = dt.date(cur.year + 1, 1, 1)
        else:
            cur = dt.date(cur.year, cur.month + 1, 1)
    return values


def safe_int(s: str):
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        return None


def safe_float(s: str):
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def decode_html(content: bytes, apparent_encoding: str = "") -> str:
    guessed = (apparent_encoding or "").strip().lower().replace("_", "-")
    if guessed.startswith("utf"):
        return content.decode("utf-8", errors="ignore")

    candidates = []
    if guessed:
        candidates.append(guessed)
    candidates.extend(["utf-8", "gb18030", "gbk", "gb2312"])

    for enc in candidates:
        try:
            text = content.decode(enc, errors="ignore")
        except Exception:
            continue
        if "<tr" in text.lower():
            return text
    return content.decode("utf-8", errors="ignore")


def parse_rows_standard(html: str, city_name: str) -> List[Tuple]:
    # 提取所有 tr
    tr_matches = re.findall(r"<tr[^>]*>.*?</tr>", html, flags=re.IGNORECASE | re.DOTALL)
    rows = []
    for i, tr in enumerate(tr_matches):
        if i == 0:
            continue
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.IGNORECASE | re.DOTALL)
        if len(tds) < 10:
            continue
        values = [strip_html(td) for td in tds]
        date_text = values[0]
        try:
            d = dt.datetime.strptime(date_text, "%Y-%m-%d").date()
        except Exception:
            continue

        rows.append(
            (
                "江西",
                city_name,
                d,
                values[2],  # Quality
                safe_int(values[1]),  # AQI
                safe_int(values[3]),  # AQI_Rank
                safe_int(values[4]),  # PM25
                safe_int(values[5]),  # PM10
                safe_int(values[7]),  # SO2
                safe_int(values[6]),  # NO2
                safe_float(values[8]),  # CO
                safe_int(values[9]),  # O3
            )
        )
    return rows


def parse_rows_rank(html: str, city_name: str) -> List[Tuple]:
    # 目前排名源与标准源字段一致，保留独立解析函数用于后续扩展。
    return parse_rows_standard(html, city_name)


def quote_sql(value):
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{text}'"


def run_mysql_sql(sql: str):
    cmd = [
        MYSQL_CLI,
        "--default-character-set=utf8mb4",
        f"-h{DB_HOST}",
        f"-P{DB_PORT}",
        f"-u{DB_USER}",
        f"-p{DB_PASSWORD}",
        DB_NAME,
    ]
    result = subprocess.run(
        cmd,
        input=sql,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-800:] if result.stderr else "mysql execute failed")


def ensure_table():
    ddl = """
    CREATE TABLE IF NOT EXISTS aqi_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        province VARCHAR(50),
        city VARCHAR(50),
        date DATE,
        Quality VARCHAR(255),
        AQI INT,
        AQI_Rank INT,
        PM25 INT,
        PM10 INT,
        SO2 INT,
        NO2 INT,
        CO FLOAT,
        O3 INT,
        UNIQUE KEY unique_record(province, city, date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    run_mysql_sql(ddl)


def upsert_rows(rows: List[Tuple], start_date: dt.date, end_date: dt.date):
    filtered = [r for r in rows if start_date <= r[2] <= end_date]
    if not filtered:
        return 0

    statements = []
    for r in filtered:
        values = ",".join(
            [
                quote_sql(r[0]),
                quote_sql(r[1]),
                quote_sql(r[2]),
                quote_sql(r[3]),
                quote_sql(r[4]),
                quote_sql(r[5]),
                quote_sql(r[6]),
                quote_sql(r[7]),
                quote_sql(r[8]),
                quote_sql(r[9]),
                quote_sql(r[10]),
                quote_sql(r[11]),
            ]
        )
        statements.append(
            "INSERT INTO aqi_data "
            "(province, city, date, Quality, AQI, AQI_Rank, PM25, PM10, SO2, NO2, CO, O3) "
            f"VALUES ({values}) "
            "ON DUPLICATE KEY UPDATE "
            "Quality=VALUES(Quality), AQI=VALUES(AQI), AQI_Rank=VALUES(AQI_Rank), "
            "PM25=VALUES(PM25), PM10=VALUES(PM10), SO2=VALUES(SO2), NO2=VALUES(NO2), "
            "CO=VALUES(CO), O3=VALUES(O3);"
        )

    run_mysql_sql("\n".join(statements))
    return len(filtered)


def crawl_by_source(city: str, start_date: dt.date, end_date: dt.date, source_code: str = "aqi_history") -> int:
    city_pinyin = CITY_PINYIN_MAP.get(city)
    if not city_pinyin:
        raise ValueError(f"不支持的城市: {city}")

    source_key = (source_code or "aqi_history").strip().lower()
    strategy = SOURCE_STRATEGIES.get(source_key, SOURCE_STRATEGIES["aqi_history"])
    parser: Callable[[str, str], List[Tuple]] = parse_rows_rank if source_key == "aqi_city_rank" else parse_rows_standard

    months = month_range(start_date, end_date)
    session = requests.Session()
    headers = strategy.get("headers", {})
    url_template = strategy.get("url_template", BASE_URL)
    sleep_sec = float(strategy.get("sleep_sec", 0.30))

    all_rows: List[Tuple] = []
    for yyyymm in months:
        url = url_template.format(city_pinyin=city_pinyin, yyyymm=yyyymm)
        resp = session.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            continue
        html = decode_html(resp.content, resp.apparent_encoding or "")
        all_rows.extend(parser(html, city))
        time.sleep(sleep_sec)

    ensure_table()
    return upsert_rows(all_rows, start_date, end_date)


def crawl(city: str, start_date: dt.date, end_date: dt.date) -> int:
    return crawl_by_source(city, start_date, end_date, "aqi_history")


def main():
    args = parse_args()
    start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    if start_date > end_date:
        raise ValueError("start-date 不能晚于 end-date")

    inserted = crawl_by_source(args.city, start_date, end_date, args.source_code)
    print(f"aqi spider finished, inserted_or_updated={inserted}")


if __name__ == "__main__":
    main()
