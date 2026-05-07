import argparse
import datetime as dt
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from spider.aqi.aqi_search_spider import fetch_live, upsert_snapshot


def parse_args():
    parser = argparse.ArgumentParser(description='AQI 实时爬虫（LIVE）')
    parser.add_argument('--city', required=True)
    parser.add_argument('--start-date', required=True)
    parser.add_argument('--end-date', required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    start_date = dt.datetime.strptime(args.start_date, '%Y-%m-%d').date()
    end_date = dt.datetime.strptime(args.end_date, '%Y-%m-%d').date()
    if start_date > end_date:
        raise ValueError('start-date 不能晚于 end-date')

    snapshot = fetch_live(args.city)
    if snapshot is None:
        print('aqi live spider finished, inserted_or_updated=0')
        return

    today = dt.date.today()
    if start_date <= today <= end_date:
        upsert_snapshot(args.city, today, snapshot)
        print('aqi live spider finished, inserted_or_updated=1')
    else:
        print('aqi live spider finished, inserted_or_updated=0')


if __name__ == '__main__':
    main()
