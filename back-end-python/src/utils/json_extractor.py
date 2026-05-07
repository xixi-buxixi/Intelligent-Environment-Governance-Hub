"""
JSON提取与清理工具

功能：
1. 从混乱的模型输出中提取JSON
2. 清理Markdown标记和多余文字
3. 修复常见JSON格式问题
"""
import re
import json
from typing import Optional, Dict, Any


class JSONExtractor:
    """JSON提取与清理器"""

    # 正则模式优先级（从精确到宽松）
    PATTERNS = [
        # 模式1: Markdown代码块中的JSON
        r'```json\s*([\s\S]*?)\s*```',
        r'```JSON\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',

        # 模式2: 花括号包围的内容（最常用）
        r'\{[\s\S]*\}',

        # 模式3: 方括号包围的列表
        r'\[[\s\S]*\]',

        # 模式4: 单行JSON对象
        r'\{[^{}]*\}',
    ]

    @staticmethod
    def extract(raw_text: str) -> Optional[Dict[str, Any]]:
        """
        多级提取JSON

        Args:
            raw_text: 原始模型输出

        Returns:
            解析后的字典或None
        """
        # Step 1: 尝试所有正则模式
        for pattern in JSONExtractor.PATTERNS:
            matches=re.findall(pattern,raw_text)
            for match in matches:
                try:
                    # 清理提取的内容
                    cleaned=JSONExtractor._clean_json_string(match)
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    continue

    @staticmethod
    def _clean_json_string(text:str)->str:
        """清理JSON字符串"""
        # 移除Markdown标记
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        # 移除前后的问候语和空白
        text = text.strip()

        # 修复常见格式问题
        # 1. 修复单引号为双引号
        text = re.sub(r"'([^']*)'", r'"\\1"', text)

        # 2. 修复缺少引号的键名
        text = re.sub(r'(\w+)(?=:)', r'"\\1"', text)

        # 3. 移除尾部逗号
        text = re.sub(r',\s*([}\]])', r'\\1', text)

        return text



















