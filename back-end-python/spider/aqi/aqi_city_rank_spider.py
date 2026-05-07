import argparse
import datetime as dt
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from spider.aqi.aqi_history_spider import crawl_by_source


def parse_args():
    parser = argparse.ArgumentParser(description="AQI 城市排名补充爬虫")
    parser.add_argument("--city", required=True, help="城市名称，例如：宜春")
    parser.add_argument("--start-date", required=True, help="开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="结束日期，格式 YYYY-MM-DD")
    return parser.parse_args()


def main():
    args = parse_args()
    start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    if start_date > end_date:
        raise ValueError("start-date 不能晚于 end-date")

    inserted = crawl_by_source(args.city, start_date, end_date, "aqi_city_rank")
    print(f"aqi city rank spider finished, inserted_or_updated={inserted}")


if __name__ == "__main__":
    main()
