"""
Agent自我反思模块

功能：
1. 定义反思结果结构
2. 提供结构化解析器
3. 支持格式自动修复
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from langchain_core.output_parsers import PydanticOutputParser


class ReflectionResult(BaseModel):
    """反思结果结构化模型"""
    score: int = Field(ge=1, le=5, description="评分1-5")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    needs_revision: bool = Field(default=False, description="是否需要修正")
    revision_hint: Optional[str] = Field(default=None, description="修正方向提示")

    @field_validator("score")
    @classmethod
    def validate(cls, v: int) -> int:
        """验证评分范围"""
        if v < 1 or v > 5:
            raise ValueError("评分必须在1-5之间")
        return v


# 创建解析器
reflection_parser = PydanticOutputParser(pydantic_object=ReflectionResult)

REFLECTION_PROMPT = """
请对以下回答进行反思评估：

原始问题：{question}
给出的回答：{answer}
使用的工具：{tools_used}

请从以下维度评估：
1. 准确性：回答是否正确？
2. 完整性：是否回答了所有要点？
3. 可靠性：是否有不确定的信息？

{format_instructions}
"""


# 辅助函数：获取完整的 Prompt 内容
def get_reflection_prompt(question: str, answer: str, tools_used: str) -> str:
    """
    生成包含格式指令的完整反思 Prompt

    Args:
        question: 原始问题
        answer: 模型给出的回答
        tools_used: 使用的工具列表或描述

    Returns:
        格式化后的 Prompt 字符串
    """
    return REFLECTION_PROMPT.format(
        question=question,
        answer=answer,
        tools_used=tools_used,
        format_instructions=reflection_parser.get_format_instructions()
    )


def get_reflection_format_instructions() -> str:
    """获取反思格式说明"""
    return reflection_parser.get_format_instructions()
