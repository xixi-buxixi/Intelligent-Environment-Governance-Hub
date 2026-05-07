"""
结构化工具实现

功能：
1. 使用Pydantic定义参数Schema
2. 自动参数验证
3. 类型安全调用

文件位置: tools/structured_tools.py
"""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any
import ast
import operator as op


class CalculatorParams(BaseModel):
    """计算器参数"""
    expression: str = Field(description="数学表达式，如 '2+3*4'")

    @field_validator("expression")
    @classmethod
    def validate_expression(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError("表达式过长")
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in v):
            raise ValueError("表达式包含非法字符")
        return v


# AST 安全解析器
_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}


def _safe_eval(expr: str) -> float:
    """AST解析，仅支持数字与基本运算符"""
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        raise ValueError("不支持的表达式（仅允许数字与 + - * / ** ()）")

    tree = ast.parse(expr, mode="eval")
    return _eval(tree.body)


def _safe_calculator_structured(expression: str) -> Dict[str, Any]:
    """
    结构化计算器实现

    注意：函数签名必须与 args_schema 的字段名匹配
    StructuredTool 会将参数作为关键字参数传入，而不是传入整个 Pydantic 对象

    Args:
        expression: 数学表达式字符串

    Returns:
        结构化结果字典
    """
    try:
        result = _safe_eval(expression)
        return {"ok": True, "data": {"value": result}, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "error": str(e)}


# 创建结构化工具
safe_calculator_structured = StructuredTool.from_function(
    name="safe_calculator_structured",
    description="安全计算器，仅支持基本数学运算。输入必须是有效的数学表达式。",
    func=_safe_calculator_structured,
    args_schema=CalculatorParams,
)