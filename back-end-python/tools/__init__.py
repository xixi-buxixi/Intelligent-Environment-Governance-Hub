"""
工具模块导出入口
"""

# 基础工具
from .basic_tools import safe_calculator, get_current_time, text_stats, unit_convert

# 高级工具
from .advanced_tools import send_email_tool

# RAG工具
from .rag_tools import rag_qa, rag_rebuild, system_health

# API工具（可选）
try:
    from .api_tools import safe_api_request
except ImportError:
    safe_api_request = None

try:
    from .live_env_tools import query_realtime_env_data
except ImportError:
    query_realtime_env_data = None


# 所有工具列表
ALL_TOOLS = [
    safe_calculator,
    get_current_time,
    text_stats,
    unit_convert,
    send_email_tool,
    rag_qa,
    rag_rebuild,
    system_health,
]

if safe_api_request:
    ALL_TOOLS.append(safe_api_request)
if query_realtime_env_data:
    ALL_TOOLS.append(query_realtime_env_data)
