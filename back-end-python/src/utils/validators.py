"""
数据验证工具

功能：
1. Pydantic模型验证
2. 部分解析支持
3. 错误报告生成
"""

from pydantic import BaseModel, ValidationError
from typing import Optional, Dict, Any, List, Type


def parse_and_validate(
        raw_json: Dict[str, Any],
        model_class: BaseModel
) -> Optional[BaseModel]:
    """
    解析并验证JSON

    Args:
        raw_json: 原始JSON字典
        model_class: Pydantic模型类

    Returns:
        验证后的模型实例或None
    """
    try:
        # Pydantic会自动：
        # 1. 类型转换（如字符串转整数）
        # 2. 字段验证
        # 3. 默认值填充
        # 4. 嵌套结构解析
        return model_class.model_validate(raw_json)
    except ValidationError as e:
        # 记录详细的验证错误
        print(f"验证失败: {e}")
        return None


def partial_parse(
        raw_json: Dict[str, Any],
        model_class: BaseModel
) -> Optional[BaseModel]:
    """
    部分解析（容错处理）

    对于缺失字段使用默认值，对于错误字段忽略
    """
    try:
        # 获取模型字段
        valid_fields = set(model_class.__pydantic_fields__.keys())

        # 移除无效字段
        filtered = {k: v for k, v in raw_json.items() if k in valid_fields}

        return model_class.model_validate(filtered)
    except Exception as e:
        print(f"部分解析失败: {e}")
        return None


def get_validation_errors(
        raw_json: Dict[str, Any],
        model_class: Type[BaseModel]
) -> List[str]:
    """
    获取验证错误详情

    Returns:
        错误信息列表
    """
    try:
        model_class.model_validate(raw_json)
        return []
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = error.get("loc", ["未知字段"])[-1]
            msg = error.get("msg", "验证失败")
            errors.append(f"字段 '{field}': {msg}")
        return errors
