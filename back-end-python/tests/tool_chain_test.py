# 使用示例
from tools.basic_tools import text_stats, safe_calculator
from tools.advanced_tools import send_email_tool

from tools.tool_chain import ToolChain, ToolStep

# 定义工具链
chain = ToolChain({
    "text_stats": text_stats,
    "safe_calculator": safe_calculator,
    "send_email": send_email_tool,
})

# 定义步骤
steps = [
    ToolStep(tool_name="text_stats", args={"text": "你好世界"}),
    ToolStep(
        tool_name="safe_calculator",
        args={"expression": "2+3"},
        depends_on=["text_stats"],  # 依赖text_stats完成
    ),
]

# 执行
result = chain.execute(steps)