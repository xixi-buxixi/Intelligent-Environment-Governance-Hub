"""
实时环境数据工具（只查询，不落库）
"""

from typing import Any, Dict, Optional
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool


JIANGXI_BASE = "https://hjzlxxfb.sthjt.jiangxi.gov.cn:9317/eipp"
WATER_ENDPOINT = f"{JIANGXI_BASE}/waterPublish/hourDataNew"
CLIMATE_ENDPOINT_CANDIDATES = [
    f"{JIANGXI_BASE}/weatherPublish/hourDataNew",
    f"{JIANGXI_BASE}/meteorologyPublish/hourDataNew",
]


def _safe_float(text: str) -> Optional[float]:
    if text is None:
        return None
    text = str(text).strip()
    if not text:
        return None
    import re
    m = re.search(r"-?\d+(?:\.\d+)?", text)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def _fetch_html(url: str, params: Dict[str, Any]) -> Optional[str]:
    try:
        resp = requests.get(
            url,
            params=params,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
            proxies={"http": None, "https": None},
        )
        if resp.status_code != 200:
            return None
        resp.encoding = "utf-8"
        return resp.text
    except Exception:
        return None


def _parse_indicator_table(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    out: Dict[str, Any] = {}
    date_input = soup.find("input", {"id": "date"})
    out["time"] = date_input.get("value") if date_input else None
    mapping = {
        "pH": "ph",
        "溶解氧": "do",
        "氨氮": "nh3n",
        "高锰酸盐指数": "codmn",
        "总磷": "tp",
        "温度": "temperature",
        "气温": "temperature",
        "湿度": "humidity",
        "风速": "windSpeed",
        "风向": "windDirection",
        "气压": "pressure",
    }
    for tr in soup.select("tr"):
        tds = tr.find_all("td")
        for i, td in enumerate(tds):
            key = td.get_text(" ", strip=True)
            if key in mapping and i + 1 < len(tds):
                val_text = tds[i + 1].get_text(" ", strip=True)
                val = _safe_float(val_text)
                out[mapping[key]] = val if val is not None else val_text
    return out


@tool
def query_realtime_env_data(data_kind: str = "water", mn: str = "A360900_2003", city_name: str = "宜春市") -> Dict[str, Any]:
    """
    查询实时环境数据（只读，不写数据库）。

    Args:
        data_kind: 查询类型，支持 water 或 climate
        mn: 监测站点编码（江西平台常用）
        city_name: 空气质量接口城市名（例如 宜春市）
    """
    kind = (data_kind or "").strip().lower()
    if kind not in {"water", "climate", "air"}:
        return {"ok": False, "data": None, "error": "data_kind 仅支持 water/climate/air"}

    if kind == "air":
        url = "https://air.cnemc.cn:18007/CityData/GetAQIDataPublishLive"
        try:
            resp = requests.get(
                url,
                params={"cityName": city_name},
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"},
                proxies={"http": None, "https": None},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"ok": True, "data": {"kind": "air", "cityName": city_name, "records": data}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": f"空气实时查询失败: {e}"}

    if kind == "water":
        html = _fetch_html(WATER_ENDPOINT, {"mn": mn})
        if not html:
            return {"ok": False, "data": None, "error": "水质实时查询失败"}
        return {"ok": True, "data": {"kind": "water", "mn": mn, "payload": _parse_indicator_table(html)}, "error": None}

    # climate: 依次尝试可用端点
    for url in CLIMATE_ENDPOINT_CANDIDATES:
        html = _fetch_html(url, {"mn": mn})
        if html:
            return {"ok": True, "data": {"kind": "climate", "mn": mn, "endpoint": url, "payload": _parse_indicator_table(html)}, "error": None}
    return {"ok": False, "data": None, "error": "气候实时查询失败（候选端点均不可用）"}
