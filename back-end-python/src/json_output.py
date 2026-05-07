"""
JSON输出提示词模板
"""
import json


JSON_OUTPUT_PROMPT = """
请严格按照以下JSON格式输出，不要添加任何其他内容：

输出要求：
1. 只输出纯JSON，不要包含任何Markdown标记（如```json）
2. 不要添加问候语、解释或额外文字
3. JSON必须符合标准格式，字段名用双引号
4. 不要输出多行JSON，保持紧凑格式

输出格式示例：
{"name": "value", "list": [1, 2, 3]}

{schema_description}

用户问题：{question}
"""
def build_schema_prompt(schema:dict)->str:
    """构建结构化Schema描述"""
    fields=[]
    for key,value in schema.items():
        if isinstance(value,dict):
            fields.append(f" \"{key}\":{json.dumps(value,ensure_ascii=False)}")
        elif isinstance(value, list):
            fields.append(f"  \"{key}\": []  # 列表类型")
        else:
            fields.append(f"  \"{key}\": \"{value}\"  # {type(value).__name__}类型")

        return "必填字段：\n" + "\n".join(fields)


















