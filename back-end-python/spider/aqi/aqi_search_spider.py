import argparse
import datetime as dt
import os
import sys
import requests

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from spider.aqi.aqi_history_spider import ensure_table, quote_sql, run_mysql_sql


def parse_args():
    parser = argparse.ArgumentParser(description='AQI 搜索实时数据爬虫（CNEMC）')
    parser.add_argument('--city', required=True)
    parser.add_argument('--start-date', required=True)
    parser.add_argument('--end-date', required=True)
    return parser.parse_args()


def safe_float(v):
    try:
        return float(v)
    except Exception:
        return None


def safe_int(v):
    try:
        return int(float(v))
    except Exception:
        return None


def fetch_live(city: str):
    url = f'https://air.cnemc.cn:18007/CityData/GetAQIDataPublishLive?cityName={city}'
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json() or []
    if not data:
        return None

    # 取实时站点AQI均值作为城市快照
    aqis = [safe_float(x.get('AQI')) for x in data if safe_float(x.get('AQI')) is not None]
    if not aqis:
        return None

    aqi = int(sum(aqis) / len(aqis))
    quality = str(data[0].get('Quality', '') or '')
    pm25 = safe_int(data[0].get('PM2_5') or data[0].get('PM2.5'))
    pm10 = safe_int(data[0].get('PM10'))
    so2 = safe_int(data[0].get('SO2'))
    no2 = safe_int(data[0].get('NO2'))
    co = safe_float(data[0].get('CO'))
    o3 = safe_int(data[0].get('O3'))
    return aqi, quality, pm25, pm10, so2, no2, co, o3


def upsert_snapshot(city: str, date_obj: dt.date, snapshot):
    aqi, quality, pm25, pm10, so2, no2, co, o3 = snapshot
    ensure_table()
    sql = (
        'INSERT INTO aqi_data '
        '(province, city, date, Quality, AQI, AQI_Rank, PM25, PM10, SO2, NO2, CO, O3) '
        f"VALUES ({quote_sql('江西')},{quote_sql(city)},{quote_sql(date_obj)},{quote_sql(quality)},{quote_sql(aqi)},NULL,{quote_sql(pm25)},{quote_sql(pm10)},{quote_sql(so2)},{quote_sql(no2)},{quote_sql(co)},{quote_sql(o3)}) "
        'ON DUPLICATE KEY UPDATE '
        'Quality=VALUES(Quality), AQI=VALUES(AQI), PM25=VALUES(PM25), PM10=VALUES(PM10), SO2=VALUES(SO2), NO2=VALUES(NO2), CO=VALUES(CO), O3=VALUES(O3);'
    )
    run_mysql_sql(sql)


def main():
    args = parse_args()
    start_date = dt.datetime.strptime(args.start_date, '%Y-%m-%d').date()
    end_date = dt.datetime.strptime(args.end_date, '%Y-%m-%d').date()
    if start_date > end_date:
        raise ValueError('start-date 不能晚于 end-date')

    snapshot = fetch_live(args.city)
    if snapshot is None:
        print('aqi search spider finished, inserted_or_updated=0')
        return

    # 实时数据按当天落库；若请求区间包含今天则计入一条
    today = dt.date.today()
    if start_date <= today <= end_date:
        upsert_snapshot(args.city, today, snapshot)
        print('aqi search spider finished, inserted_or_updated=1')
    else:
        print('aqi search spider finished, inserted_or_updated=0')


if __name__ == '__main__':
    main()
