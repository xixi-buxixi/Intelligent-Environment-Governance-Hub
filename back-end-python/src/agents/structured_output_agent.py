"""
结构化输出Agent

功能：
1. 自动格式约束
2. 多层级解析兜底
3. 错误修复重试

文件位置: src/agents/structured_output_agent.py
"""

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import Optional
from langchain_core.output_parsers import PydanticOutputParser
from ..parsers.robust_parser import RobustJSONParser
from ..llm.factory import get_chat_model


class StructureOutputAgent:
    """结构化输出Agent"""

    def __init__(self, output_model: BaseModel):
        """
        初始化

        Args:
            output_model: 期望的输出结构（Pydantic模型）
        """
        self.llm = get_chat_model()
        self.output_model = output_model
        self.parser = RobustJSONParser(output_model, self.llm)
        # 创建提示模板（自动包含格式说明）
        format_parser = PydanticOutputParser(pydantic_object=output_model)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是结构化输出专家。{format_instructions}"),
            ("human", "{question}")
        ]).partial(format_instructions=format_parser.get_format_instructions())

    def analyze(self,question:str)->Optional[BaseModel]:
        """分析并返回结构化结果"""
        # 生成提示
        prompt_value=self.prompt.format_prompt(question=question)
        # 调用LLM
        response = self.llm.invoke(prompt_value.to_messages())

        # 使用多层级解析器
        return self.parser.parse(response.content)










