"""
工具链编排模块
"""

from typing import List, Dict, Any, Callable
from pydantic import BaseModel


class ToolStep(BaseModel):
    """工具步骤定义"""
    tool_name: str
    args: Dict[str, Any] = {}
    depends_on: List[str] = []  #依赖的前置工具
    condition: str = ""  #执行条件


class ToolChain:
    """
    工具链编排器

    功能：
    1. 定义多工具执行顺序
    2. 处理工具间依赖
    3. 管理中间结果传递
    """

    def __init__(self, tools: Dict[str, Callable]):
        """
        初始化工具链

        Args:
            tools: 工具名称到函数的映射
        """
        self.tools = tools
        self.results: Dict[str, Any] = {}

    def execute(self, steps: List[ToolStep]) -> Dict[str, Any]:
        """
        执行工具链

        Args:
            steps: 工具步骤列表

        Returns:
            所有步骤的执行结果
        """
        self.results = {}

        for step in steps:
            #检查依赖是否满足
            for dep in step.depends_on:
                if dep not in self.results:
                    return {
                        "ok": False,
                        "error": f"依赖未满足：{step.tool_name} 需要 {dep}",
                        "completed": list(self.results.keys()),
                    }

                #构建参数（可能包含前置工具结果）
                args=step.args.copy()
                for dep in step.depends_on:
                    # 将前置结果传入参数
                    args[f"{dep}_result"]=self.results[dep]

                #执行工具
                tool=self.tools.get(step.tool_name)
                if not tool:
                    return{
                        "ok": False,
                        "error": f"工具不存在：{step.tool_name}",
                        "completed": list(self.results.keys()),
                    }
                try:
                    result=tool.invoke(args) if hasattr(tool,"invoke") else tool(**args)
                    self.results[step.tool_name]=result
                except Exception as e:
                    return {
                        "ok": False,
                        "error": f"工具执行失败：{step.tool_name} - {e}",
                        "completed": list(self.results.keys()),
                    }
            return {
                "ok": True,
                "results": self.results,
                "completed": list(self.results.keys()),
            }




























