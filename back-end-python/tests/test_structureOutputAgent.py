"""
结构化工具Agent测试

功能：
1. 使用结构化工具
2. 自动参数验证
3. 类型安全调用

文件位置: tests/test_structureOutputAgent.py
"""

import pytest
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from typing import Dict, Any

from tools.structured_tools import safe_calculator_structured
from tools.basic_tools import get_current_time, text_stats, unit_convert
from tools.rag_tools import rag_qa, system_health
from src.config import Config


class TestStructureOutputAgent:
    """结构化工具Agent测试"""

    def _create_structured_agent(self):
        """创建结构化工具Agent

        使用 OpenAI 兼容方式连接阿里云 DashScope API
        """
        # 使用 ChatOpenAI + base_url 连接阿里云
        llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_API_BASE
        )

        # 结构化工具列表
        tools = [
            safe_calculator_structured,
            get_current_time,
            text_stats,
            unit_convert,
            rag_qa,
            system_health,
        ]

        system_prompt = """
你是结构化输出助手。必须使用工具完成任务：
- 数学计算：使用 safe_calculator_structured
- 时间查询：使用 get_current_time
- 文本统计：使用 text_stats
- 知识问答：使用 rag_qa

工具参数必须符合Schema定义。
"""

        agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)
        return agent

    def test_run_structured_agent_calculation(self):
        """测试数学计算"""
        executor = self._create_structured_agent()
        result = executor.invoke({"messages": [HumanMessage(content="计算 25 * 4 + 10")]})
        assert result is not None
        assert "messages" in result
        print(f"计算结果: {result['messages'][-1].content}")

    def test_run_structured_agent_time(self):
        """测试时间查询"""
        executor = self._create_structured_agent()
        result = executor.invoke({"messages": [HumanMessage(content="现在几点了?")]})
        assert result is not None
        assert "messages" in result
        print(f"时间查询结果: {result['messages'][-1].content}")

    def test_run_structured_agent_text_stats(self):
        """测试文本统计"""
        executor = self._create_structured_agent()
        result = executor.invoke({"messages": [HumanMessage(content="统计 'Hello World Python Programming' 的文本信息")]})
        assert result is not None
        assert "messages" in result
        print(f"文本统计结果: {result['messages'][-1].content}")