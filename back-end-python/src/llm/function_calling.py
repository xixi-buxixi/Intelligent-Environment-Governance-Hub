"""
通义千问Function Calling封装

功能：
1. 工具Schema定义
2. 函数调用封装
3. 结果解析
"""
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List, Optional
import json

from src.config import Config


class FunctionCallingWrapper:
    """Function Calling封装器"""

    def __init__(self):
        self.llm=ChatOpenAI(
            model=Config.LLM_MODEL,
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_API_BASE
        )
        self.tools_schema:List[Dict]=[]

    def register_tool(self,name:str,description:str,parameters:Dict)->None:
        """注册工具Schema"""
        tool = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        }
        self.tools_schema.append(tool)

    def invoke(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        调用LLM

        Returns:
            function_call对象或None
        """
        llm_with_tools = self.llm.bind_tools(self.tools_schema)
        response = llm_with_tools.invoke([HumanMessage(content=prompt)])


        # 检查是否有function_call
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_call = response.tool_calls[0]
            return {
                "name": tool_call["name"],
                "arguments": tool_call["args"],
            }

        return None


# 使用示例
if __name__ == "__main__":
    wrapper = FunctionCallingWrapper()

    # 注册工具
    wrapper.register_tool(
        name="send_email",
        description="发送邮件通知",
        parameters={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "收件人邮箱"},
                "subject": {"type": "string", "description": "邮件主题"},
                "body": {"type": "string", "description": "邮件正文"},
            },
            "required": ["to", "subject", "body"],
        }
    )

    # 调用
    result = wrapper.invoke("请给test@example.com发送一封关于项目进展的邮件")
    print(result)
    # {'name': 'send_email', 'arguments': {'to': 'test@example.com', 'subject': '项目进展', 'body': '...'}}
















