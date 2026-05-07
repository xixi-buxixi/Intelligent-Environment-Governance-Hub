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


BASE_URL = "http://sthjj.yichun.gov.cn/ycssthjj/"


def parse_args():
    parser = argparse.ArgumentParser(description="生态环境新闻抓取")
    parser.add_argument("--city", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    return parser.parse_args()


def parse_publish_time(text: str, default_date: dt.date) -> str:
    m = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text or "")
    if not m:
        return default_date.isoformat()
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return dt.date(y, mo, d).isoformat()
    except Exception:
        return default_date.isoformat()


def fetch_news(city: str, start_date: dt.date, end_date: dt.date) -> List[Dict]:
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
        if not title or len(title) < 6 or not href:
            continue
        if "javascript:" in href.lower():
            continue
        if "ycssthjj" not in href and "/art/" not in href:
            continue
        url = urljoin(BASE_URL, href)
        if url in seen:
            continue
        seen.add(url)
        publish_date = parse_publish_time(title, end_date)
        d = dt.date.fromisoformat(publish_date)
        if d < start_date or d > end_date:
            continue
        rows.append(
            {
                "date": publish_date,
                "city": city,
                "title": title,
                "publishTime": publish_date,
                "source": "宜春市生态环境局",
                "url": url,
            }
        )
    return rows[:200]


def main():
    args = parse_args()
    start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    rows = fetch_news(args.city, start_date, end_date)
    inserted = save_raw_rows("env_news", args.city, rows, date_key="date")
    print(f"env news spider finished, inserted={inserted}")


if __name__ == "__main__":
    main()
