# LangChain JSON格式输出优化方案

> 本文档基于项目 `D:\My\python\project\Langchain-demo\project` 的实际结构编写

## 一、问题背景

在Agent工程实践中，让大模型输出固定JSON格式是一个常见的难题。许多开发者简单地在提示词中添加"只输出JSON"的要求，但实际项目中模型输出往往不可控：

- 输出包含Markdown标记（如 ` ```json `）
- 输出包含问候语或解释性文字
- JSON格式不规范（缺少引号、字段名错误）
- 嵌套结构解析失败

## 二、完整解决方案架构

```
┌─────────────────────────────────────────────────────────────┐
│                    JSON输出控制层级                           │
├─────────────────────────────────────────────────────────────┤
│  Level 1: 提示词约束（基础层，可靠性低）                       │
│  Level 2: 正则提取与清理（后处理层，兼容性强）                  │
│  Level 3: OutputParser重试机制（LangChain内置）               │
│  Level 4: Pydantic结构化验证（Python原生方案）                 │
│  Level 5: Function Calling / Tools（最可靠方案）              │
└─────────────────────────────────────────────────────────────┘
```

## 三、项目文件结构概览

```
D:\My\python\project\Langchain-demo\project
├── main.py                      # 主程序入口
├── app.py                       # Flask API服务
├── demo_agent.py                # Agent演示脚本
├── demo_advanced_agent.py       # 高级Agent演示
├── demo_complete_agent.py       # 完整Agent演示
├── src/
│   ├── config.py                # 配置管理
│   ├── agent.py                 # 基础Agent实现
│   ├── advanced_agent.py        # 高级Agent（带记忆）
│   ├── complete_agent.py        # 完整Agent（所有功能）
│   ├── reflection.py            # 反思模块（待优化）
│   ├── state_manager.py         # 状态持久化
│   ├── document_processor.py    # 文档处理
│   ├── vectorstore.py           # 向量存储管理
│   └── rag_chain.py             # RAG链实现
├── tools/
│   ├── __init__.py              # 工具模块入口
│   ├── basic_tools.py           # 基础工具定义
│   ├── advanced_tools.py        # 高级工具（结构化参数）
│   ├── rag_tools.py             # RAG相关工具
│   ├── schemas.py               # 参数Schema定义
│   ├── tool_chain.py            # 工具链编排
│   ├── validation.py            # 输入验证
│   ├── error_handling.py        # 错误处理
│   └── api_tools.py             # API工具
├── tests/
│   ├── test_tools.py            # 工具测试
│   └── test_advanced_agent.py   # Agent测试
└── advanced/
    ├── conversational_rag.py    # 对话式RAG
    └── hybrid_retriever.py      # 混合检索器
```

---

## 四、Level 1: 提示词约束（基础层）

### 4.1 基础提示词模板

**文件位置：可新建 `src/prompts/json_output.py` 或整合到现有模块**

```python
# 文件位置: src/prompts/json_output.py（新建）
"""
JSON输出提示词模板
"""

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
```

### 4.2 结构化Schema提示

**文件位置：同上 `src/prompts/json_output.py`**

```python
# 文件位置: src/prompts/json_output.py
import json

def build_schema_prompt(schema: dict) -> str:
    """构建结构化Schema描述"""
    fields = []
    for key, value in schema.items():
        if isinstance(value, dict):
            fields.append(f"  \"{key}\": {json.dumps(value, ensure_ascii=False)}")
        elif isinstance(value, list):
            fields.append(f"  \"{key}\": []  # 列表类型")
        else:
            fields.append(f"  \"{key}\": \"{value}\"  # {type(value).__name__}类型")
    
    return "必填字段：\n" + "\n".join(fields)
```

### 4.3 局限性说明

提示词约束可靠性约60-70%，常见失败场景：
- 模型"礼貌性"添加问候语
- 复杂嵌套结构时格式混乱
- 模型版本更新后行为变化

---

## 五、Level 2: 正则提取与清理（后处理层）

### 5.1 多级正则提取策略

**文件位置：新建 `src/utils/json_extractor.py`**

```python
# 文件位置: src/utils/json_extractor.py（新建）
"""
JSON提取与清理工具

功能：
1. 从混乱的模型输出中提取JSON
2. 清理Markdown标记和多余文字
3. 修复常见JSON格式问题
"""

import re
import json


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
    def extract(raw_text: str) -> dict | None:
        """
        多级提取JSON
        
        Args:
            raw_text: 原始模型输出
            
        Returns:
            解析后的字典或None
        """
        # Step 1: 尝试所有正则模式
        for pattern in JSONExtractor.PATTERNS:
            matches = re.findall(pattern, raw_text)
            for match in matches:
                try:
                    # 清理提取的内容
                    cleaned = JSONExtractor._clean_json_string(match)
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    continue
        
        # Step 2: 如果所有模式都失败，尝试全文解析
        try:
            cleaned = JSONExtractor._clean_json_string(raw_text)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def _clean_json_string(text: str) -> str:
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
```

### 5.2 使用示例

**文件位置：新建 `demo_json_extractor.py`**

```python
# 文件位置: demo_json_extractor.py（新建）
"""
JSON提取器演示脚本
运行方式: python demo_json_extractor.py
"""

from src.utils.json_extractor import JSONExtractor

# 原始模型输出（包含Markdown标记和问候语）
raw_output = """
好的，我来为您分析这个问题。

```json
{
    "score": 4,
    "issues": ["回答不完整"],
    "needs_revision": true
}
希望这个结果对您有帮助！
"""

# 提取JSON

result = JSONExtractor.extract(raw_output)
print(result)
#输出: {'score': 4, 'issues': ['回答不完整'], 'needs_revision': True}
```



## 六、Level 3: LangChain OutputParser（重试机制）

### 6.1 PydanticOutputParser基础用法

**文件位置：优化现有 `src/reflection.py`**

```
# 文件位置: src/reflection.py（优化版）
"""
Agent自我反思模块

功能：
1. 定义反思结果结构
2. 提供结构化解析器
3. 支持格式自动修复
"""

from pydantic import BaseModel, Field, field_validator
from typing import List
from langchain.output_parsers import PydanticOutputParser


class ReflectionResult(BaseModel):
    """反思结果结构化模型"""
    score: int = Field(ge=1, le=5, description="评分1-5")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    needs_revision: bool = Field(default=False, description="是否需要修正")
    
    @field_validator("score")
    @classmethod
    def validate_score(cls, v: int) -> int:
        """验证评分范围"""
        if v < 1 or v > 5:
            raise ValueError("评分必须在1-5之间")
        return v


# 创建解析器
reflection_parser = PydanticOutputParser(pydantic_object=ReflectionResult)

# 提示词（包含格式说明）
REFLECTION_PROMPT = """
请对以下回答进行反思评估：

原始问题：{question}
给出的回答：{answer}
使用的工具：{tools_used}

{format_instructions}
"""
```

### 6.2 OutputFixingParser（自动修复机制）

**文件位置：新建 `src/parsers/robust_parser.py`**

```python
# 文件位置: src/parsers/robust_parser.py（新建）
"""
多层级JSON解析器

整合多种解析策略：
1. 正则提取
2. Pydantic验证
3. OutputFixingParser修复
4. 部分解析兜底
"""

from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from pydantic import BaseModel, ValidationError
from typing import Optional

from src.utils.json_extractor import JSONExtractor
from src.config import Config
from langchain_community.chat_models.tongyi import ChatTongyi


class RobustJSONParser:
    """
    多层级JSON解析器
    
    解析流程：
    Level 1 → Level 2 → Level 3 → Level 4
    （从简单到复杂，逐层兜底）
    """
    
    def __init__(self, model_class: BaseModel, llm=None):
        self.model_class = model_class
        self.llm = llm or ChatTongyi(
            model_name=Config.LLM_MODEL,
            dashscope_api_key=Config.OPENAI_API_KEY,
        )
        
        # 创建各层级解析器
        self.pydantic_parser = PydanticOutputParser(pydantic_object=model_class)
        self.fixing_parser = OutputFixingParser.from_llm(
            parser=self.pydantic_parser,
            llm=self.llm,
        )
    
    def parse(self, raw_output: str) -> Optional[BaseModel]:
        """多层级解析"""
        
        # Level 2: 正则提取
        extracted = JSONExtractor.extract(raw_output)
        if not extracted:
            return None
        
        # Level 4: Pydantic验证
        try:
            return self.model_class(**extracted)
        except ValidationError:
            pass
        
        # Level 3: OutputFixingParser修复
        try:
            return self.fixing_parser.parse(raw_output)
        except Exception:
            pass
        
        # 最终兜底：部分解析
        return self._partial_parse(extracted)
    
    def _partial_parse(self, raw_json: dict) -> Optional[BaseModel]:
        """部分解析（容错处理）"""
        try:
            # 获取模型字段
            valid_fields = set(self.model_class.__pydantic_fields__.keys())
            
            # 移除无效字段
            filtered = {k: v for k, v in raw_json.items() if k in valid_fields}
            
            # 使用默认值填充缺失字段
            return self.model_class(**filtered)
        except Exception:
            return None
```

### 6.3 RetryOutputParser（重试机制）

**文件位置：同上 `src/parsers/robust_parser.py`**

```python
# 文件位置: src/parsers/robust_parser.py（追加）
from langchain.output_parsers import RetryOutputParser
from langchain_core.exceptions import OutputParserException


def parse_with_retry(
    parser: RetryOutputParser,
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
            # 继续重试
    return None
```

### 6.4 完整OutputParser集成示例

**文件位置：新建 `src/agents/structured_output_agent.py`**

```python
# 文件位置: src/agents/structured_output_agent.py（新建）
"""
结构化输出Agent

功能：
1. 自动格式约束
2. 多层级解析兜底
3. 错误修复重试
"""

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import Optional

from src.parsers.robust_parser import RobustJSONParser
from src.config import Config


class StructuredOutputAgent:
    """结构化输出Agent"""
    
    def __init__(self, output_model: BaseModel):
        """
        初始化
        
        Args:
            output_model: 期望的输出结构（Pydantic模型）
        """
        self.llm = ChatTongyi(
            model_name=Config.LLM_MODEL,
            dashscope_api_key=Config.OPENAI_API_KEY,
        )
        self.output_model = output_model
        self.parser = RobustJSONParser(output_model, self.llm)
        
        # 创建提示模板（自动包含格式说明）
        from langchain.output_parsers import PydanticOutputParser
        format_parser = PydanticOutputParser(pydantic_object=output_model)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是结构化输出专家。{format_instructions}"),
            ("human", "{question}"),
        ]).partial(format_instructions=format_parser.get_format_instructions())
    
    def analyze(self, question: str) -> Optional[BaseModel]:
        """分析并返回结构化结果"""
        # 生成提示
        prompt_value = self.prompt.format_prompt(question=question)
        
        # 调用LLM
        response = self.llm.invoke(prompt_value.to_messages())
        
        # 使用多层级解析器
        return self.parser.parse(response.content)
```

---

## 七、Level 4: Pydantic结构化验证（Python原生方案）

### 7.1 Pydantic模型定义

**文件位置：优化现有 `tools/schemas.py`**

```python
# 文件位置: tools/schemas.py（优化版）
"""
工具参数模型定义

功能：
1. 定义结构化参数Schema
2. 自动类型验证
3. 字段约束检查
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class EmailParams(BaseModel):
    """邮件发送参数"""
    to: str = Field(description="收件人邮箱")
    subject: str = Field(description="邮件主题")
    body: str = Field(description="邮件正文")
    priority: str = Field(default="normal", description="优先级：high/normal/low")

    @field_validator("priority")
    @classmethod
    def _check_priority(cls, v: str) -> str:
        if v not in ["high", "normal", "low"]:
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
    tools_needed: List[str] = Field(description="需要使用的工具列表")
    execution_order: List[str] = Field(description="执行顺序")
    reasoning: str = Field(description="选择这些工具的原因")
    
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
    score: int = Field(ge=1, le=5, description="评分1-5")
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    needs_revision: bool = Field(default=False)
    revision_content: Optional[str] = Field(default=None)
```

### 7.2 解析与验证流程

**文件位置：新建 `src/utils/validators.py`**

```python
# 文件位置: src/utils/validators.py（新建）
"""
数据验证工具

功能：
1. Pydantic模型验证
2. 部分解析支持
3. 错误报告生成
"""

from pydantic import BaseModel, ValidationError
from typing import Optional, Dict, Any


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
        return model_class(**raw_json)
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
        
        return model_class(**filtered)
    except Exception as e:
        print(f"部分解析失败: {e}")
        return None


def get_validation_errors(
    raw_json: Dict[str, Any],
    model_class: BaseModel
) -> List[str]:
    """
    获取验证错误详情
    
    Returns:
        错误信息列表
    """
    try:
        model_class(**raw_json)
        return []
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = error.get("loc", ["未知字段"])[-1]
            msg = error.get("msg", "验证失败")
            errors.append(f"字段 '{field}': {msg}")
        return errors


# 使用示例
if __name__ == "__main__":
    from tools.schemas import AgentReflection
    
    raw_output = {
        "score": "4",  # 字符串会被自动转换为整数
        "issues": ["回答不完整"],
        "needs_revision": "true",  # 会自动转为bool
        "invalid_field": "ignored",  # 无效字段会被忽略
    }
    
    result = partial_parse(raw_output, AgentReflection)
    print(result)
    # AgentReflection(score=4, issues=['回答不完整'], suggestions=[], needs_revision=True)
```

---

## 八、Level 5: Function Calling / Tools（最可靠方案）

### 8.1 原理说明

Function Calling（工具调用）是OpenAI等主流模型提供的底层接口：
- 模型不再自由输出文本
- 而是在底层生成结构化的参数对象
- 由系统执行函数并返回结果

这种方式将JSON生成从"文本生成"转变为"参数生成"，格式可靠性达到95%以上。

### 8.2 LangChain StructuredTool实现

**文件位置：参考现有 `tools/advanced_tools.py` 结构**

```python
# 文件位置: tools/structured_tools.py（新建）
"""
结构化工具实现

功能：
1. 使用Pydantic定义参数Schema
2. 自动参数验证
3. 类型安全调用
"""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Dict, Any


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


def _safe_calculator_structured(params: CalculatorParams) -> Dict[str, Any]:
    """结构化计算器实现"""
    import ast
    import operator as op
    
    _OPS = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
    }
    
    def _eval(node):
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        raise ValueError("不支持的表达式")
    
    try:
        tree = ast.parse(params.expression, mode="eval")
        result = _eval(tree.body)
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
```

### 8.3 使用Tool绑定的Agent

**文件位置：参考现有 `src/advanced_agent.py` 结构**

```python
# 文件位置: src/structured_agent.py（新建）
"""
结构化工具Agent

功能：
1. 使用结构化工具
2. 自动参数验证
3. 类型安全调用
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_community.chat_models.tongyi import ChatTongyi
from typing import Dict, Any

from tools.structured_tools import safe_calculator_structured
from tools.basic_tools import get_current_time, text_stats, unit_convert
from tools.rag_tools import rag_qa, system_health
from src.config import Config


def create_structured_agent():
    """创建结构化工具Agent"""
    llm = ChatTongyi(
        model_name=Config.LLM_MODEL,
        dashscope_api_key=Config.OPENAI_API_KEY,
    )
    
    # 结构化工具列表
    tools = [
        safe_calculator_structured,
        get_current_time,
        text_stats,
        unit_convert,
        rag_qa,
        system_health,
    ]
    
    system_prompt = """
    你是结构化输出助手。必须使用工具完成任务：
    - 数学计算：使用 safe_calculator_structured
    - 时间查询：使用 get_current_time
    - 文本统计：使用 text_stats
    - 知识问答：使用 rag_qa
    
    工具参数必须符合Schema定义。
    """
    
    agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)
    return agent


def run_structured_agent(question: str) -> Dict[str, Any]:
    """运行结构化Agent"""
    executor = create_structured_agent()
    return executor.invoke({"messages": [HumanMessage(content=question)]})
```

### 8.4 通义千问Function Calling示例

**文件位置：新建 `src/llm/function_calling.py`**

```python
# 文件位置: src/llm/function_calling.py（新建）
"""
通义千问Function Calling封装

功能：
1. 工具Schema定义
2. 函数调用封装
3. 结果解析
"""

from langchain_community.chat_models.tongyi import ChatTongyi
from typing import Dict, Any, List, Optional
import json

from src.config import Config


class FunctionCallingWrapper:
    """Function Calling封装器"""
    
    def __init__(self):
        self.llm = ChatTongyi(
            model_name=Config.LLM_MODEL,
            dashscope_api_key=Config.OPENAI_API_KEY,
        )
        self.tools_schema: List[Dict] = []
    
    def register_tool(self, name: str, description: str, parameters: Dict) -> None:
        """注册工具Schema"""
        tool = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        }
        self.tools_schema.append(tool)
    
    def invoke(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        调用LLM
        
        Returns:
            function_call对象或None
        """
        response = self.llm.invoke(prompt, functions=self.tools_schema)
        
        # 检查是否有function_call
        if hasattr(response, "additional_kwargs"):
            function_call = response.additional_kwargs.get("function_call")
            if function_call:
                return {
                    "name": function_call.get("name"),
                    "arguments": json.loads(function_call.get("arguments", "{}")),
                }
        
        return None


# 使用示例
if __name__ == "__main__":
    wrapper = FunctionCallingWrapper()
    
    # 注册工具
    wrapper.register_tool(
        name="send_email",
        description="发送邮件通知",
        parameters={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "收件人邮箱"},
                "subject": {"type": "string", "description": "邮件主题"},
                "body": {"type": "string", "description": "邮件正文"},
            },
            "required": ["to", "subject", "body"],
        }
    )
    
    # 调用
    result = wrapper.invoke("请给test@example.com发送一封关于项目进展的邮件")
    print(result)
    # {'name': 'send_email', 'arguments': {'to': 'test@example.com', 'subject': '项目进展', 'body': '...'}}
```

---

## 九、综合最佳实践方案

### 9.1 推荐架构

**文件位置：整合到 `src/parsers/robust_parser.py`**

```python
# 文件位置: src/parsers/robust_parser.py（完整版）
"""
多层级JSON解析器 - 完整实现

解析流程：
Level 2（正则） → Level 4（Pydantic） → Level 3（修复） → 兜底（部分解析）
"""

from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from pydantic import BaseModel, ValidationError
from typing import Optional, Dict, Any

from src.utils.json_extractor import JSONExtractor
from src.utils.validators import partial_parse
from src.config import Config
from langchain_community.chat_models.tongyi import ChatTongyi


class RobustJSONParser:
    """
    多层级JSON解析器
    
    使用示例：
    >>> from tools.schemas import AgentReflection
    >>> parser = RobustJSONParser(AgentReflection)
    >>> result = parser.parse(raw_llm_output)
    """
    
    def __init__(self, model_class: BaseModel, llm=None):
        """
        初始化
        
        Args:
            model_class: Pydantic模型类
            llm: 语言模型（用于修复解析）
        """
        self.model_class = model_class
        self.llm = llm or ChatTongyi(
            model_name=Config.LLM_MODEL,
            dashscope_api_key=Config.OPENAI_API_KEY,
        )
        
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
        
        # Level 4: Pydantic直接验证
        try:
            return self.model_class(**extracted)
        except ValidationError:
            pass
        
        # Level 3: OutputFixingParser修复
        try:
            return self.fixing_parser.parse(raw_output)
        except Exception:
            pass
        
        # 最终兜底：部分解析
        return partial_parse(extracted, self.model_class)
    
    def get_format_instructions(self) -> str:
        """获取格式说明（用于提示词）"""
        return self.pydantic_parser.get_format_instructions()
```

### 9.2 完整使用示例

**文件位置：新建 `demo_robust_parser.py`**

```python
# 文件位置: demo_robust_parser.py（新建）
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
```
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

## 十、项目现有代码优化建议

### 10.1 reflection.py优化

**文件位置：`src/reflection.py`（当前仅定义提示词，建议增强）**

```

# 文件位置: src/reflection.py（完整优化版）
"""
Agent自我反思模块

功能：
1. 定义反思结果结构（Pydantic）
2. 提供结构化解析器
3. 支持格式自动修复
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from langchain.output_parsers import PydanticOutputParser


class ReflectionResult(BaseModel):
    """反思结果结构化模型"""
    score: int = Field(ge=1, le=5, description="评分1-5")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    needs_revision: bool = Field(default=False, description="是否需要修正")
    revision_hint: Optional[str] = Field(default=None, description="修正方向提示")
    
    @field_validator("score")
    @classmethod
    def validate_score(cls, v: int) -> int:
        """验证评分范围"""
        if v < 1 or v > 5:
            raise ValueError("评分必须在1-5之间")
        return v


# 创建解析器
reflection_parser = PydanticOutputParser(pydantic_object=ReflectionResult)

# 提示词（包含格式说明）
REFLECTION_PROMPT = """
请对以下回答进行反思评估：

原始问题：{question}
给出的回答：{answer}
使用的工具：{tools_used}

请从以下维度评估：
1. **准确性**：回答是否正确？工具结果是否被正确引用？
2. **完整性**：回答是否完整回答了用户的问题？
3. **清晰度**：回答是否清晰易懂？
4. **可靠性**：是否有不确定的信息被当作确定信息？

{format_instructions}
"""

# 便捷函数
def get_reflection_format_instructions() -> str:
    """获取反思格式说明"""
    return reflection_parser.get_format_instructions()
```

### 10.2 advanced_agent.py中的chat_with_reflection优化

**文件位置：`src/advanced_agent.py`（优化现有方法）**

```python
# 文件位置: src/advanced_agent.py（chat_with_reflection方法优化）
"""
在现有AdvancedAgent类中替换chat_with_reflection方法
"""

from typing import Dict, Any
from src.reflection import reflection_parser, ReflectionResult, get_reflection_format_instructions
from src.parsers.robust_parser import RobustJSONParser


def chat_with_reflection(self, question: str) -> Dict[str, Any]:
    """
    带自我反思的对话（优化版）
    
    使用多层级解析器确保JSON格式正确
    
    Args:
        question: 用户问题
        
    Returns:
        包含回答和反思结果的字典
    """
    # 1. 首次回答
    initial_result = self.chat(question)
    initial_answer = initial_result["answer"]
    tool_calls = initial_result["tool_calls"]
    
    # 2. 构建反思提示（使用结构化解析器）
    reflection_prompt = f"""
    原始问题：{question}
    给出的回答：{initial_answer}
    使用的工具：{tool_calls}
    
    {get_reflection_format_instructions()}
    """
    
    # 3. 调用LLM生成反思
    response = self.llm.invoke([
        {"role": "system", "content": "你是质量评估专家，严格按JSON格式输出。"},
        {"role": "user", "content": reflection_prompt},
    ])
    
    # 4. 使用多层级解析器解析（关键改进）
    parser = RobustJSONParser(ReflectionResult, self.llm)
    reflection_result = parser.parse(response.content)
    
    # 5. 根据反思结果决定是否修正
    final_answer = initial_answer
    revised = False
    
    if reflection_result and reflection_result.needs_revision:
        # 提取修正建议
        revision_prompt = f"""
        根据评估建议修正回答：
        
        发现的问题：{reflection_result.issues}
        改进建议：{reflection_result.suggestions}
        
        原始回答：{initial_answer}
        
        请给出修正后的回答。
        """
        
        revision_result = self.chat(revision_prompt)
        final_answer = revision_result["answer"]
        revised = True
        
        # 记录修正到记忆
        self.memory.add_message("system", f"回答已根据反思修正")
    
    # 6. 返回完整结果
    return {
        "answer": final_answer,
        "initial_answer": initial_answer,
        "reflection": reflection_result.model_dump() if reflection_result else None,
        "needs_revision": reflection_result.needs_revision if reflection_result else False,
        "revised": revised,
        "tool_calls": tool_calls,
        "history": self.memory.get_history(),
    }
```

### 10.3 schemas.py扩展

**文件位置：`tools/schemas.py`（添加更多Schema）**

```python
# 文件位置: tools/schemas.py（追加内容）
"""
追加更多结构化Schema定义
"""

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
```

---

## 十一、方案对比总结

| 方案 | 可靠性 | 实现复杂度 | 适用场景 | 推荐文件位置 |
|------|--------|------------|----------|--------------|
| 提示词约束 | 60-70% | 低 | 简单场景，辅助手段 | `src/prompts/json_output.py` |
| 正则提取 | 80-85% | 中 | 后处理兜底 | `src/utils/json_extractor.py` |
| OutputFixingParser | 85-90% | 中 | LangChain项目 | `src/parsers/robust_parser.py` |
| Pydantic验证 | 90-95% | 中 | 类型安全 | `tools/schemas.py` |
| Function Calling | 95%+ | 高 | 最可靠方案 | `src/llm/function_calling.py` |

**推荐组合方案**：
```
Function Calling (首选) → Pydantic验证 → 正则提取兜底
```

**新增文件清单**：
- `src/utils/json_extractor.py` - JSON提取器
- `src/utils/validators.py` - 数据验证工具
- `src/parsers/robust_parser.py` - 多层级解析器
- `src/prompts/json_output.py` - JSON提示词模板
- `src/llm/function_calling.py` - Function Calling封装
- `src/agents/structured_output_agent.py` - 结构化输出Agent
- `tools/structured_tools.py` - 结构化工具定义
- `demo_robust_parser.py` - 解析器演示

**需优化文件清单**：
- `src/reflection.py` - 添加Pydantic模型和解析器
- `src/advanced_agent.py` - 优化chat_with_reflection方法
- `tools/schemas.py` - 扩展Schema定义

---

## 十二、参考资源

- [LangChain Output Parsers](https://python.langchain.com/docs/modules/model_io/output_parsers/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [通义千问API文档](https://help.aliyun.com/document_detail/2712195.html)

---

*文档版本: 1.1*
*更新日期: 2026-04-18*
*适用项目: Langchain-demo-project*
*项目路径: D:\My\python\project\Langchain-demo\project*