"""
API工具实现（带安全控制）
"""

from langchain_core.tools import tool
from typing import Dict, Any
import requests
import time
from urllib.parse import urlparse

class APISafetyConfig:
    """API安全配置"""
    ALLOWED_DOMAINS=[

    ]
    MAX_TIMEOUT = 30
    MAX_RETRIES = 3

@tool
def safe_api_request(url:str,method:str="GET",params:Dict=None)->Dict[str,Any]:
    """
    安全API请求工具

    使用场景：
    - 需要调用外部API获取数据
    - 天气查询、数据获取等

    Args:
        url: API URL（必须是白名单域名）
        method: HTTP方法（GET/POST）
        params: 请求参数

    Returns:
        dict: API响应结果
    """
    # 1. 域名白名单检查
    parsed=urlparse(url)
    domain=parsed.netloc

    if domain not in APISafetyConfig.ALLOWED_DOMAINS:
        return {
            "ok": False,
            "data": None,
            "error": f"域名 {domain} 不在白名单中，不允许访问",
        }
    # 2. 方法限制
    if method not in ["GET","POST"]:
        return {
            "ok":False,
            "data":None,
            "error":f"不支持的方法：{method}",
        }
    # 3. 执行请求
    retries = 0
    while retries < APISafetyConfig.MAX_RETRIES:
        try:
            start_time = time.time()
            response = requests.request(
                method,
                url,
                params=params,
                timeout=APISafetyConfig.MAX_TIMEOUT,
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                return {
                    "ok": True,
                    "data": response.json(),
                    "elapsed": elapsed,
                    "error": None,
                }
            else:
                return {
                    "ok": False,
                    "data": None,
                    "error": f"HTTP {response.status_code}",
                }

        except requests.Timeout:
            retries += 1
        except Exception as e:
            return {
                "ok": False,
                "data": None,
                "error": str(e),
            }

    return {
        "ok": False,
        "data": None,
        "error": f"请求超时（{retries}次重试后）",
    }


























