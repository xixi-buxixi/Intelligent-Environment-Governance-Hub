"""
工具参数模型定义

功能：
1. 定义结构化参数Schema
2. 自动类型验证
3. 字段约束检查
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any

class EmailParams(BaseModel):
    """邮件发送参数"""
    to: str = Field(description="收件人邮箱")
    subject: str = Field(description="邮件主题")
    body: str = Field(description="邮件正文")
    priority: str = Field(default="normal", description="优先级：high/normal/low")

    @field_validator("priority")
    @classmethod
    def _check_priority(cls,v:str)->str:
        if v not in ["high","normal","low"]:
            raise ValueError("优先级只能是high/normal/low")
        return v

    @field_validator("to")
    @classmethod
    def _check_email(cls, v: str) -> str:
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError("邮箱格式无效")
        return v

class RAGQAParams(BaseModel):
    """RAG问答参数"""
    question: str = Field(description="用户问题")
    top_k: int = Field(default=3, description="返回文档数量")

    @field_validator("top_k")
    @classmethod
    def _check_top_k(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("top_k 必须在 1-10 之间")
        return v



class ToolExecutionPlan(BaseModel):
    """工具执行计划结构"""
    tools_needed:List[str]=Field(description="需要使用的工具列表")
    execution_order:List[str]=Field(description="执行顺序")
    reasoning:str=Field(description="选择这些工具的原因")

    @field_validator("tools_needed")
    @classmethod
    def validate_tools(cls, v: List[str]) -> List[str]:
        """验证工具名称有效性"""
        valid_tools = ["safe_calculator", "text_stats", "unit_convert", "rag_qa", "system_health"]
        for tool in v:
            if tool not in valid_tools:
                raise ValueError(f"无效工具: {tool}")
        return v

class AgentReflection(BaseModel):
    """Agent反思结果"""
    score:int=Field(ge=1,le=5,description="评分1-5")
    issues:List[str]=Field(default_factory=list)
    suggestions:List[str]=Field(default_factory=list)
    needs_revision:bool=Field(default=False)
    revision_content:Optional[str]=Field(default=None)




class ReflectionParams(BaseModel):
    """反思评估参数"""
    question: str = Field(description="原始问题")
    answer: str = Field(description="待评估的回答")
    tools_used: List[str] = Field(default_factory=list, description="使用的工具列表")


class PlanningParams(BaseModel):
    """任务规划参数"""
    user_request: str = Field(description="用户请求")
    available_tools: List[str] = Field(description="可用工具列表")
    context: str = Field(default="", description="上下文信息")


class ToolChainParams(BaseModel):
    """工具链执行参数"""
    tool_sequence: List[str] = Field(description="工具执行顺序")
    inputs: Dict[str, Any] = Field(description="各工具的输入参数")
    expected_output: str = Field(default="", description="预期输出类型")






















