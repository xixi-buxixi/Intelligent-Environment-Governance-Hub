import argparse
import datetime as dt
import os
import re
import sys
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from spider.raw_store import save_raw_rows


API_BASE_URL = "https://hjzlxxfb.sthjt.jiangxi.gov.cn:9317/eipp/waterPublish/hourDataNew"
STATION_CODES = {
    "A360900_2003": "丰城小港口",
    "A360900_2004": "高安市青州村",
    "A360900_2005": "良田村",
    "A360900_2006": "三洪村",
    "A360900_2007": "肖江江口",
    "A360900_2008": "港口",
}
INDICATOR_MAP = {
    "pH": "ph",
    "溶解氧": "doValue",
    "氨氮": "nh3n",
    "高锰酸盐指数": "codmn",
    "总磷": "tp",
}


def parse_args():
    parser = argparse.ArgumentParser(description="水质监测数据抓取")
    parser.add_argument("--city", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    return parser.parse_args()


def parse_float(text: str) -> Optional[float]:
    m = re.search(r"-?\d+(?:\.\d+)?", text or "")
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def fetch_station_row(city: str, mn: str, station: str, start_date: dt.date, end_date: dt.date) -> Optional[Dict]:
    try:
        resp = requests.get(API_BASE_URL, params={"mn": mn}, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return None
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        date_input = soup.find("input", {"id": "date"})
        raw_time = date_input.get("value") if date_input else ""
        measure_time = raw_time[:19] if raw_time else dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        d = dt.datetime.strptime(measure_time, "%Y-%m-%d %H:%M:%S").date()
        if d < start_date or d > end_date:
            return None

        row = {
            "date": d.isoformat(),
            "city": city,
            "station": station,
            "measureTime": measure_time,
            "ph": None,
            "doValue": None,
            "nh3n": None,
            "codmn": None,
            "tp": None,
            "wqi": None,
        }

        for tr in soup.select("tr"):
            tds = tr.find_all("td")
            for idx, td in enumerate(tds):
                key = td.get_text(strip=True)
                if key in INDICATOR_MAP and idx + 1 < len(tds):
                    val = parse_float(tds[idx + 1].get_text(" ", strip=True))
                    row[INDICATOR_MAP[key]] = val

        if row["ph"] is not None and row["doValue"] is not None:
            row["wqi"] = round((7.0 - abs(row["ph"] - 7.0)) * 10 + row["doValue"], 2)
        return row
    except Exception:
        return None


def main():
    args = parse_args()
    start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    rows: List[Dict] = []
    for mn, station in STATION_CODES.items():
        one = fetch_station_row(args.city, mn, station, start_date, end_date)
        if one:
            rows.append(one)
    inserted = save_raw_rows("water_quality", args.city, rows, date_key="date")
    print(f"water quality spider finished, inserted={inserted}")


if __name__ == "__main__":
    main()
