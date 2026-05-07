"""
基础工具示例

文件位置: tools/basic_tools.py

学习要点：
1. @tool装饰器是最简单的工具定义方式
2. 函数的docstring会成为工具的描述（LLM会阅读）
3. 参数类型注解帮助LLM正确传参
4. 工具应该有明确的输入输出
"""

from langchain_core.tools import tool
from datetime import datetime
import math
import re
import ast
import operator as op
from pydantic import BaseModel, Field, field_validator


_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}

def _safe_eval(expr:str)->float:
    """AST解析，仅支持数字与 + - * / ** ()"""
    def _eval(node):
        if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        raise ValueError("不支持的表达式（仅允许数字与 + - * / ** ()）")
    tree=ast.parse(expr,mode="eval")
    return _eval(tree.body)
@tool
def safe_calculator(expression:str)->dict:
    """
    安全计算器：仅支持数字与 + - * / ** ()。


    使用场景：
    - 用户需要进行具体的数值计算时
    - 用户询问涉及数学公式的结果时

    Args:
        expression: 数学表达式，如 "25*4+10"、"(1+2)**3"。

    Returns:
        dict: 结构化结果，包含 ok/data/error。


    """

    try:
        value = _safe_eval(expression)
        return {"ok": True, "data": {"value": value}, "error": None}
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": f"计算失败：{e}。请检查表达式，只能使用数字与 + - * / ** ()",
        }


@tool
def get_current_time(format_str:str="%Y-%m-%d %H:%M:%S")->str:
    """
    获取当前时间。

    什么时候用：
    - 用户问“现在几点/今天几号”
    - 需要时间戳写日志/生成报告

    Args:
        format_str: strftime 格式字符串。

    Returns:
        格式化后的当前时间字符串。
    """
    return datetime.now().strftime(format_str)


@tool
def text_stats(text:str)->dict:
    """
    统计文本中的单词数、字符数、句子数。

    使用场景：
    - 用户需要统计文本中单词数、字符数、句子数时

    Args:
        text: 待统计的文本。

    Returns:
        dict: 结构化统计结果（更利于模型后续使用）。
    """
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    english_words = len(re.findall(r"[A-Za-z]+", text))
    sentences = len([s for s in re.split(r"[。！？.!?]+", text) if s.strip()])

    return{
        "ok":True,
        "data":{
            "chinese_chars":chinese_chars,
            "english_words":english_words,
            "total_chars": len(text),
            "sentences_estimate": sentences,
        },
        "error":None,
    }



@tool
def unit_convert(value:float,from_unit:str,to_unit:str)->dict:
    """
    单位转换工具。支持温度(C/F)和长度(km/miles)转换。

    使用场景：
    - 用户需要进行单位换算时
    - 用户询问温度或长度的转换结果

    Args:
        value: 要转换的数值
        from_unit: 源单位（C/F/km/miles）
        to_unit: 目标单位（C/F/km/miles）

    Returns:
        dict: 结构化结果，包含转换后的值
    """
    conversions = {
        ("C", "F"): lambda x: x * 9 / 5 + 32,
        ("F", "C"): lambda x: (x - 32) * 5 / 9,
        ("km", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x * 1.60934,
    }

    key=(from_unit,to_unit)
    if key not in conversions:
        return {
            "ok": False,
            "data": None,
            "error": f"不支持从 {from_unit} 到 {to_unit} 的转换。支持的转换：C↔F, km↔miles"
        }
    try:
        result = conversions[key](value)
        return {"ok": True, "data": {"value": result, "from": from_unit, "to": to_unit}, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "error": f"转换失败: {e}"}




















