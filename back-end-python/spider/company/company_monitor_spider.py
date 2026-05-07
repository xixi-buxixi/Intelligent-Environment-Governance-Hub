import argparse
import datetime as dt
import os
import re
import sys
from typing import Dict, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from spider.raw_store import save_raw_rows


BASE_URL = "http://sthjj.yichun.gov.cn/ycssthjj/wryjc/pc/list.html"


def parse_args():
    parser = argparse.ArgumentParser(description="企业监测数据抓取")
    parser.add_argument("--city", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    return parser.parse_args()


def parse_ym(text: str):
    m = re.search(r"(20\d{2})年(\d{1,2})月", text or "")
    if not m:
        return None
    y, mo = int(m.group(1)), int(m.group(2))
    try:
        return dt.date(y, mo, 1)
    except Exception:
        return None


def fetch_company_rows(city: str, start_date: dt.date, end_date: dt.date) -> List[Dict]:
    resp = requests.get(BASE_URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        return []
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    rows: List[Dict] = []
    seen = set()
    for a in soup.select("a[href]"):
        title = a.get_text(strip=True)
        href = a.get("href", "").strip()
        if "重点排污单位执法监测" not in title:
            continue
        url = urljoin(BASE_URL, href)
        if not href or url in seen:
            continue
        seen.add(url)
        d = parse_ym(title) or end_date
        if d < start_date or d > end_date:
            continue
        rows.append(
            {
                "date": d.isoformat(),
                "city": city,
                "company": title,
                "indicator": "执法监测文件",
                "value": url,
                "measureTime": d.isoformat(),
            }
        )
    return rows[:200]


def main():
    args = parse_args()
    start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    rows = fetch_company_rows(args.city, start_date, end_date)
    inserted = save_raw_rows("company_monitor", args.city, rows, date_key="date")
    print(f"company monitor spider finished, inserted={inserted}")


if __name__ == "__main__":
    main()
