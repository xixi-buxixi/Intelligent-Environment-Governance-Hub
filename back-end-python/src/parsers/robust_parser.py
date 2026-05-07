"""
多层级JSON解析器

整合多种解析策略：
1. 正则提取
2. Pydantic验证
3. OutputFixingParser修复
4. 部分解析兜底


解析流程：
Level 2（正则） → Level 4（Pydantic） → Level 3（修复） → 兜底（部分解析）


文件位置: src/parsers/robust_parser.py
"""
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, ValidationError
from typing import Optional

from ..utils.json_extractor import JSONExtractor
from ..llm.factory import get_chat_model
from langchain_classic.output_parsers import OutputFixingParser

from langchain_core.exceptions import OutputParserException


class RobustJSONParser:
    """
    多层级JSON解析器

    解析流程：
    Level 1 → Level 2 → Level 3 → Level 4
    （从简单到复杂，逐层兜底）
    """

    def __init__(self, model_class: BaseModel, llm=None):
        """
        初始化

        Args:
            model_class: Pydantic模型类
            llm: 语言模型（用于修复解析）
        """
        self.model_class = model_class
        self.llm = llm or get_chat_model()

        # 创建各层级解析器
        self.pydantic_parser = PydanticOutputParser(pydantic_object=model_class)
        self.fixing_parser = OutputFixingParser.from_llm(
            parser=self.pydantic_parser,
            llm=self.llm,
        )

    def parse(self, raw_output: str) -> Optional[BaseModel]:
        """
        多层级解析

        Args:
            raw_output: 原始模型输出

        Returns:
            解析后的模型实例或None
        """

        # Level 2: 正则提取
        extracted = JSONExtractor.extract(raw_output)
        if not extracted:
            return None

        # Level 4: Pydantic验证
        try:
            return self.model_class.model_validate(extracted)
        except ValidationError:
            pass

        # Level 3: OutputFixingParser修复
        try:
            return self.fixing_parser.parse(raw_output)
        except Exception:
            pass

        # 最终兜底：部分解析
        return self._partial_parse(extracted)

    def get_format_instructions(self) -> str:
        """获取格式说明（用于提示词）"""
        return self.pydantic_parser.get_format_instructions()

    def _partial_parse(self, raw_json: dict) -> Optional[BaseModel]:
        """部分解析（容错处理）"""
        try:
            # 获取模型字段
            valid_fields = set(self.model_class.__pydantic_fields__.keys())
            # 移除无效字段
            filtered = {k: v for k, v in raw_json.items() if k in valid_fields}
            # 使用默认值填充缺失字段
            return self.model_class.model_validate(filtered)
        except Exception:
            return None


def parse_with_retry(
        parser,
        prompt_value: str,
        raw_output: str,
        max_retries: int = 3
) -> Optional[BaseModel]:
    """
    带重试的解析流程

    流程：
    1. 尝试解析原始输出
    2. 如果失败，将错误信息+原始输出作为新提示
    3. 让LLM重新生成符合格式的输出
    4. 最多重试max_retries次
    """
    for attempt in range(max_retries):
        try:
            return parser.parse_with_prompt(raw_output, prompt_value)
        except OutputParserException as e:
            if attempt == max_retries - 1:
                raise
    return None
