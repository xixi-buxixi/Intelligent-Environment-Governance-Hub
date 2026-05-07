import argparse
import datetime as dt
import os
import re
import sys
from typing import Dict, List

import requests

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from spider.raw_store import save_raw_rows


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


def parse_args():
    parser = argparse.ArgumentParser(description="历史气象抓取")
    parser.add_argument("--city", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    return parser.parse_args()


def decode_html(content: bytes) -> str:
    for enc in ["utf-8", "gb18030", "gbk", "gb2312"]:
        try:
            return content.decode(enc, errors="ignore")
        except Exception:
            continue
    return content.decode("utf-8", errors="ignore")


def month_range(start_date: dt.date, end_date: dt.date):
    cur = dt.date(start_date.year, start_date.month, 1)
    end = dt.date(end_date.year, end_date.month, 1)
    while cur <= end:
        yield cur.strftime("%Y%m")
        if cur.month == 12:
            cur = dt.date(cur.year + 1, 1, 1)
        else:
            cur = dt.date(cur.year, cur.month + 1, 1)


def parse_temp(temp_text: str):
    nums = re.findall(r"-?\d+", temp_text or "")
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    if len(nums) == 1:
        v = int(nums[0])
        return v, None
    return None, None


def parse_month(city: str, yyyymm: str) -> List[Dict]:
    city_code = CITY_PINYIN_MAP.get(city)
    if not city_code:
        return []
    url = f"https://www.tianqihoubao.com/lishi/{city_code}/month/{yyyymm}.html"
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        return []
    html = decode_html(resp.content)
    html = re.sub(r"<br[^>]*>", " / ", html, flags=re.IGNORECASE)
    rows = re.findall(r"<tr[^>]*>.*?</tr>", html, flags=re.IGNORECASE | re.DOTALL)
    result: List[Dict] = []
    for idx, tr in enumerate(rows):
        if idx == 0:
            continue
        cols = re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.IGNORECASE | re.DOTALL)
        if len(cols) < 4:
            continue
        date_text = re.sub(r"<[^>]+>", "", cols[0]).strip()
        weather_text = re.sub(r"<[^>]+>", "", cols[1]).strip()
        temp_text = re.sub(r"<[^>]+>", "", cols[2]).strip()
        wind_text = re.sub(r"<[^>]+>", "", cols[3]).strip()
        d = None
        try:
            d = dt.datetime.strptime(date_text, "%Y年%m月%d日").date()
        except Exception:
            try:
                d = dt.datetime.strptime(date_text, "%Y-%m-%d").date()
            except Exception:
                continue
        temp_high, temp_low = parse_temp(temp_text)
        result.append(
            {
                "date": d.isoformat(),
                "city": city,
                "tempHigh": temp_high,
                "tempLow": temp_low,
                "weather": weather_text,
                "wind": wind_text,
                "humidity": None,
            }
        )
    return result


def main():
    args = parse_args()
    start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    all_rows: List[Dict] = []
    for yyyymm in month_range(start_date, end_date):
        all_rows.extend(parse_month(args.city, yyyymm))
    filtered = [r for r in all_rows if start_date <= dt.date.fromisoformat(r["date"]) <= end_date]
    inserted = save_raw_rows("weather_history", args.city, filtered, date_key="date")
    print(f"weather history spider finished, inserted={inserted}")


if __name__ == "__main__":
    main()
