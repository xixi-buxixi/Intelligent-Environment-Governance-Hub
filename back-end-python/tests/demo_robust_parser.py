"""
多层级解析器演示
运行方式: python demo_robust_parser.py
"""

from pydantic import BaseModel, Field
from typing import List

from src.parsers.robust_parser import RobustJSONParser
from src.config import Config
from langchain_community.chat_models.tongyi import ChatTongyi

# 定义期望的输出结构
class AnalysisResult(BaseModel):
    """分析结果结构"""
    score: int = Field(ge=1, le=5)
    issues: List[str]
    suggestions: List[str]
    needs_revision: bool


def main():
    # 创建解析器
    parser = RobustJSONParser(
        model_class=AnalysisResult,
        llm=ChatTongyi(
            model_name=Config.LLM_MODEL,
            dashscope_api_key=Config.OPENAI_API_KEY,
        ),
    )

    # 模拟混乱的模型输出
    raw_output = """
    好的！让我来分析这个回答...

    评分是4分，因为有些小问题。
    以下是JSON结果：
    ```json
    {
        "score": 4,
        "issues": ["回答略显简单", "缺少具体数据"],
        "suggestions": ["补充数据支撑", "增加案例"],
        "needs_revision": true
    }
希望能帮到您！
"""

    # 解析
    result = parser.parse(raw_output)

    print("=" * 50)
    print("解析结果:")
    print(f"  score: {result.score}")
    print(f"  issues: {result.issues}")
    print(f"  suggestions: {result.suggestions}")
    print(f"  needs_revision: {result.needs_revision}")
    print("=" * 50)
if __name__ == "__main__":
    main()
















