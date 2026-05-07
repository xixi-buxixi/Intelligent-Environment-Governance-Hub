"""
Agent实现
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from src.llm.factory import get_chat_model

from tools import safe_calculator, get_current_time, text_stats, unit_convert
from src.config import Config
def create_environment_agent():
    """创建环境小助手Agent"""
    # LLM配置
    llm = get_chat_model()
    # 工具列表
    tools = [safe_calculator, get_current_time, text_stats, unit_convert]
    #Prompt
    system_prompt = (
        "你是环境小助手。遇到计算/统计/时间/单位转换问题必须调用对应工具。"
        "工具结果为准，不要编造。不确定的信息要说不知道。"
    )

    #agent创建
    agent=create_agent(model=llm, tools=tools, system_prompt=system_prompt)


    return agent

def run_agent(question:str)->dict:
    """
    运行 Agent（新版本）

    说明：
    - create_agent 的 invoke 输入通常是 {"messages": [...]} 的形式
    - 返回值是一个 state dict，其中包含 messages（含工具调用过程）
    """
    executor = create_environment_agent()
    return executor.invoke({"messages":[HumanMessage(content=question)]})

















