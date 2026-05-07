"""
JSON提取器演示脚本
运行方式: python demo_json_extractor.py
"""


from src.utils import JSONExtractor

# 原始模型输出（包含Markdown标记和问候语）
raw_output = """
好的，我来为您分析这个问题。

```json
{
    "score": 4,
    "issues": ["回答不完整"],
    "needs_revision": true
}
"""

result = JSONExtractor.extract(raw_output)
print(result)