"""
工具与LLM集成
"""

from langchain_community.chat_models.tongyi import ChatTongyi
from tools.basic_tools import safe_calculator, get_current_time, text_stats
from src.config import Config
from langchain_core.messages import HumanMessage, ToolMessage

def create_llm_with_tools():
    """创建带工具绑定的LLM"""
    llm = ChatTongyi(model_name="qwen-plus", dashscope_api_key=Config.OPENAI_API_KEY)
    tools=[safe_calculator,get_current_time,text_stats]
    llm_with_tools = llm.bind_tools(tools)
    return llm_with_tools,tools


def run_tool_call_loop(llm_with_tools,tools_list:list,user_question:str)->str:
    """
    工具调用闭环实现

    流程：
    1. LLM生成tool_calls或直接回答
    2. 执行工具
    3. ToolMessage回填
    4. 循环直到无tool_calls
    """
    tools_by_name = {t.name: t for t in tools_list}
    messages = [HumanMessage(content=user_question)]

    while True:
        ai = llm_with_tools.invoke(messages)

        # 无tool_calls：直接回答
        if not getattr(ai, "tool_calls", None):
            return ai.content

        # 有tool_calls：执行并回填
        messages.append(ai)
        for call in ai.tool_calls:
            tool_name = call["name"]
            tool_args = call.get("args", {})
            tool = tools_by_name[tool_name]

            result = tool.invoke(tool_args)
            messages.append(ToolMessage(content=str(result),
                                        tool_call_id=call["id"]))
































