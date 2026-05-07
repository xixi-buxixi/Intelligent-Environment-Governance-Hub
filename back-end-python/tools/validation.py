"""
工具输入验证模块
"""

from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict
from functools import wraps


class ToolInputValidator:
    """
    工具输入验证器

    功能：
    1. 参数类型验证
    2. 参数范围验证
    3. 安全性检查
    """
    @staticmethod
    def validate_expression(expr:str)->bool:
        """验证数学表达式安全性"""
        #检查长度
        if len(expr)>100:
            return False
        #检查非法字符
        allowed_chars=set("0123456789+-*/() .")
        if not all(c in allowed_chars for c in expr):
            return False
        return True
    @staticmethod
    def validate_text_length(text:str,max_length:int=10000)->bool:
        """验证文本长度"""
        return len(text) <= max_length

    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    # 使用验证器增强工具

#error_hangding.py已有功能
# from tools.basic_tools import safe_calculator, text_stats
#
# def safe_calculator_with_validation(expression:str)->Dict[str,Any]:
#     """带验证的安全计算器"""
#     # 先验证输入
#     if not ToolInputValidator.validate_expression(expression):
#         return {
#             "ok": False,
#             "data": None,
#             "error": "表达式不安全或过长，请使用简单的数学运算",
#         }
#
#     # 再调用原工具
#     return safe_calculator.invoke({"expression": expression})
#
# def text_stats_with_validation(text:str,max_length:int=10000)->Dict[str,Any]:
#     """带验证的文本统计"""
#     if not ToolInputValidator.validate_text_length(text, max_length):
#         return {
#             "ok": False,
#             "data": None,
#             "error": f"文本过长（{len(text)} > {max_length}）",
#         }
#     return text_stats.invoke({"text": text})
































