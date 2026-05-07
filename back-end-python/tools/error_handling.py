"""
工具错误处理模块
"""

from typing import Dict, Any, Callable, Optional
from functools import wraps
import time


class ToolErrorHandler:
    """
    工具错误处理器

    功能：
    1. 自动重试
    2. 超时控制
    3. 错误报告
    """

    def __init__(
            self,
            max_retries: int = 3,
            timeout: float = 30.0,
            retry_delay: float = 1.0,
    ):
        """
        初始化错误处理器

        Args:
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
            retry_delay: 重试间隔（秒）
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_delay = retry_delay

    def wrap_tool(self, tool_func: Callable) -> Callable:
        """
        包装工具函数，添加错误处理

        Args:
            tool_func: 原工具函数

        Returns:
            包装后的函数
        """
        #@wraps(tool_func) 的作用就是把原函数的名字、文档说明等“身份信息”复制给新函数。
        @wraps(tool_func)
        def wrapped(*args, **kwargs) -> Dict[str, Any]:
            # *args：代表位置参数。它可以把所有按照位置传入的参数（比如1, 2, 3）全部打包成一个元组接收进来。
            # 不管你传了多少个参数，它都能接住。** kwargs：代表关键字参数。
            # 它可以把所有带名字的参数（比如name = "张三", age = 18）全部打包成一个字典接收进来。
            # 合在一起的效果：这意味着rapped是一个 “万能接口” 。
            # 不管原来的tool_func需要什么样的参数，wrapped都可以照单全收，然后原封不动地转交给tool_func。
            retries = 0
            last_error = None

            while retries < self.max_retries:
                try:
                    # 执行工具
                    start_time = time.time()
                    result = tool_func(*args, **kwargs)
                    elapsed = time.time() - start_time

                    # 检查超时
                    if elapsed > self.timeout:
                        return {
                            "ok": False,
                            "data": None,
                            "error": f"工具执行超时（{elapsed:.1f}s > {self.timeout}s）",
                            "elapsed": elapsed,
                        }

                    return result  # 成功了，直接返回结果
                except Exception as e:
                    retries += 1
                    last_error = str(e)

                    if retries < self.max_retries:
                        time.sleep(self.retry_delay)

            # 注意：这里的 return 必须在 while 循环外面！
            # 只有循环结束（重试机会用光）才会走到这里
            return {
                "ok": False,
                "data": None,
                "error": f"工具执行失败（{retries}次重试后）：{last_error}",
                "retries": retries,
            }

        return wrapped


error_handler = ToolErrorHandler(max_retries=3, timeout=30.0)

# 包装现有工具
from tools.basic_tools import safe_calculator, get_current_time

safe_calculator_with_retry = error_handler.wrap_tool(safe_calculator)
