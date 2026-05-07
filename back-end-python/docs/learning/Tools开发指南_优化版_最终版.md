# LangChain Tools 开发指南（优化版｜最终版）

> **目标**：学完后你能**独立设计、编写、调试、测试、上线**可用的 Tools，并能把 Tools 接入 LLM/Agent，让模型稳定地“会用工具做事”。
>
> **适用项目背景**：基于深度学习的宜春市环境检测数据分析可视化项目。  
> - 文档主体以 **LangChain 1.0+（推荐）** 的写法为准（尤其是 Agent 部分）。  
> - 如果你仍在使用 **LangChain 0.3.x**：Tools/闭环部分基本一致；Agent 部分请参考文末的“兼容说明/替代方案”。

---

## 更新记录（2026-04-11）

你提供的修复记录已合并进本文档，确保“照着做就能跑通”：

1. **pytest 默认 addopts 的兼容性修复**  
   - 问题现象：`pytest` 报错 `unrecognized arguments: --cov=src --cov-report=term-missing`  
   - 根因：`pyproject.toml` 默认加了 coverage 参数，但环境未安装 `pytest-cov`  
   - 处理：把默认 `addopts` 改为安全的 `-v`；如果需要 coverage，再显式安装 `pytest-cov` 并开启

2. **safe_calculator 失败修复**  
   - 问题现象：`safe_calculator.invoke(...)` 返回 `ok=False`  
   - 根因：`ast.parse(expr, model="eval")` 参数写错（应为 `mode`）  
   - 处理：修正为 `ast.parse(expr, mode="eval")`

3. **验证通过**（你已完成）  
   - 运行：`python -m pytest tests/test_tools.py::TestSafeCalculator -q`  
   - 结果：`2 passed`

---

## 项目结构一览（更新版）

```
D:\My\python\project\Langchain-demo\project\
│
├── tools/                          # 工具模块目录
│   ├── __init__.py                 # 工具导出入口（已实现）
│   ├── basic_tools.py              # 基础工具实现（已实现）
│   ├── schemas.py                  # Pydantic参数模型（已实现）
│   ├── advanced_tools.py           # 高级工具（已实现）
│   ├── tool_integration.py         # 工具与LLM集成（已实现）
│   ├── demo_tool_loop.py           # 工具调用演示脚本（已实现）
│   ├── api_tools.py                # API工具（空文件，待实现）
│   └── tool_manager.py             # 工具管理器（空文件，待实现）
│
├── src/                            # 核心源代码目录
│   ├── __init__.py                 # 包初始化
│   ├── config.py                   # 配置管理（API密钥等）
│   ├── document_processor.py       # 文档处理器
│   ├── vectorstore.py              # 向量存储管理
│   └── rag_chain.py                # RAG链实现
│
├── data/                           # 数据目录
│   └── knowledge/                  # 知识库文档
│       ├── 垃圾分类指南.txt
│       ├── 环境保护基础知识.txt
│       └── 节能减排小知识.txt
│
├── chroma_db/                      # Chroma向量数据库
│   └── ...
│
├── advanced/                       # 高级功能模块
│   ├── __init__.py
│   ├── conversational_rag.py       # 对话式RAG（已实现）
│   └── hybrid_retriever.py         # 混合检索器（已实现）
│
├── logs/                           # 日志目录
│   └── app.log
│
├── .tiktoken_cache/                # tiktoken缓存
│
├── main.py                         # 主入口（命令行）
├── app.py                          # Flask Web应用
├── download_tiktoken.py            # tiktoken下载脚本
├── .env                            # 环境变量（API密钥）
├── pyproject.toml                  # 项目依赖配置
├── requirement.txt                 # 依赖列表（备用）
├── RAG开发指南.md                   # RAG相关文档
└── Tools开发指南_优化版_最终版.md    # 本文档
```

---

## 目录

1. [Tools 概念与定位](#1-tools-概念与定位)
2. [现有工具文件详解](#2-现有工具文件详解)
3. [工具开发规范](#3-工具开发规范)
4. [阶段 1：基础工具开发](#4-阶段-1基础工具开发)
5. [阶段 2：结构化参数工具](#5-阶段-2结构化参数工具)
6. [阶段 3：LLM 工具调用闭环](#6-阶段-3llm-工具调用闭环)
7. [阶段 4：Agent 集成（LangChain 1.0+）](#7-阶段-4agent-集成langchain-10)
8. [与现有 RAG 项目集成](#8-与现有-rag-项目集成)
9. [调试与测试（重要更新）](#9-调试与测试重要更新)
10. [练习清单](#10-练习清单)
11. [附录：关键配置文件与兼容说明](#11-附录关键配置文件与兼容说明)

---

## 1. Tools 概念与定位

### 1.1 一句话定义

**Tool = 一段可被 LLM “按协议调用”的函数能力**。  
LLM 负责“决定要不要用、用哪个、怎么传参”；工具负责“把事情做完并返回结果”。

### 1.2 Tools vs RAG vs Agent

| 类型 | 核心能力 | 典型用途 | 文件位置示例 |
|------|----------|----------|--------------|
| **RAG** | 检索知识 → 拼上下文 → 回答 | 查询信息、问答 | `src/rag_chain.py` |
| **Tools** | 执行动作/调用外部能力 | 计算、API调用、发邮件 | `tools/basic_tools.py` |
| **Agent** | 多轮规划 + 工具协作 | 复杂任务编排 | `src/agent.py`（本章提供） |

---

## 2. 现有工具文件详解

### 2.1 工具目录结构

```
位置: D:\My\python\project\Langchain-demo\project\tools\

tools/
├── __init__.py         # 导出工具
├── basic_tools.py      # 基础工具实现
├── schemas.py          # Pydantic参数模型
├── advanced_tools.py   # 高级工具（结构化参数）
├── tool_integration.py # 工具与LLM集成（闭环）
├── demo_tool_loop.py   # 工具调用演示
├── api_tools.py        # 空文件（待实现）
└── tool_manager.py     # 空文件（待实现）
```

### 2.2 `tools/__init__.py`详解

```python
【文件: tools/__init__.py】
【完整路径: D:\My\python\project\Langchain-demo\project\tools\__init__.py】
【行数: 1-2】

# 第1行：导入基础工具（已包含unit_convert）
from .basic_tools import safe_calculator, get_current_time, text_stats, unit_convert

# 第2行：ToolManager注释掉（尚未实现）
# from .tool_manager import ToolManager  # ToolManager 尚未实现
```

**要点**：`__init__.py` 负责“对外统一导出”，以后其他地方只需要 `from tools import ...`。

### 2.3 `tools/basic_tools.py`详解

#### 2.3.1 安全计算器辅助函数（AST白名单）

```python
【文件: tools/basic_tools.py】
【完整路径: D:\My\python\project\Langchain-demo\project\tools\basic_tools.py】
【行数: 22-41】

_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}

def _safe_eval(expr: str) -> float:
    """AST解析，仅支持数字与 + - * / ** ()"""
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        raise ValueError("不支持的表达式（仅允许数字与 + - * / ** ()）")

    # 关键：这里是 mode，不是 model
    tree = ast.parse(expr, mode="eval")
    return _eval(tree.body)
```

**通俗解释**：  
这段代码把字符串表达式“拆成结构（AST）”，然后只允许你白名单里的运算符（+ - * / ** 和负号），其他任何东西（变量、函数、导入、系统命令）都拒绝，从而避免 `eval()` 的安全风险。

> ✅ 正确：`ast.parse(expr, mode="eval")`  
> ❌ 常见错误：`ast.parse(expr, model="eval")`（会直接报错，导致计算器总失败）

#### 2.3.2 安全计算器工具定义

```python
【文件: tools/basic_tools.py】
【完整路径: D:\My\python\project\Langchain-demo\project\tools\basic_tools.py】
【行数: 42-69】

@tool
def safe_calculator(expression: str) -> dict:
    """
    安全计算器：仅支持数字与 + - * / ** ()。

    使用场景：
    - 用户需要进行数值计算时
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
```

#### 2.3.3 获取当前时间工具

```python
【文件: tools/basic_tools.py】
【完整路径: D:\My\python\project\Langchain-demo\project\tools\basic_tools.py】
【行数: 72-87】

@tool
def get_current_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前时间。

    使用场景：
    - 用户问"现在几点/今天几号"
    - 需要时间戳写日志/生成报告

    Args:
        format_str: strftime 格式字符串。

    Returns:
        格式化后的当前时间字符串。
    """
    return datetime.now().strftime(format_str)
```

#### 2.3.4 文本统计工具

```python
【文件: tools/basic_tools.py】
【完整路径: D:\My\python\project\Langchain-demo\project\tools\basic_tools.py】
【行数: 90-117】

@tool
def text_stats(text: str) -> dict:
    """
    统计文本中的单词数、字符数、句子数。

    使用场景：
    - 用户需要统计文本信息时

    Args:
        text: 待统计的文本。

    Returns:
        dict: 结构化统计结果（更利于模型后续使用）。
    """
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    english_words = len(re.findall(r"[A-Za-z]+", text))
    sentences = len([s for s in re.split(r"[。！？.!?]+", text) if s.strip()])

    return {
        "ok": True,
        "data": {
            "chinese_chars": chinese_chars,
            "english_words": english_words,
            "total_chars": len(text),
            "sentences_estimate": sentences,
        },
        "error": None,
    }
```

#### 2.3.5 单位转换工具（已实现）

```python
【文件: tools/basic_tools.py】
【完整路径: D:\My\python\project\Langchain-demo\project\tools\basic_tools.py】
【行数: 121-156】

@tool
def unit_convert(value: float, from_unit: str, to_unit: str) -> dict:
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
        ("C", "F"): lambda x: x * 9/5 + 32,
        ("F", "C"): lambda x: (x - 32) * 5/9,
        ("km", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x * 1.60934,
    }

    key = (from_unit, to_unit)
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
```

### 2.4 `tools/schemas.py`详解（已实现）

```python
【文件: tools/schemas.py】
【完整路径: D:\My\python\project\Langchain-demo\project\tools\schemas.py】
【行数: 1-64】

"""
工具参数模型定义
"""

from pydantic import BaseModel, Field, field_validator

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
```

### 2.5 `tools/advanced_tools.py`详解（已实现）

```python
【文件: tools/advanced_tools.py】
【完整路径: D:\My\python\project\Langchain-demo\project\tools\advanced_tools.py】
【行数: 1-27】

"""
高级工具实现（结构化参数）
"""

from langchain_core.tools import StructuredTool
from .schemas import EmailParams, RAGQAParams


def _send_email(params: EmailParams) -> dict:
    """邮件发送实现"""
    # TODO: 接入真实邮件API
    return {
        "ok": True,
        "data": {
            "to": params.to,
            "subject": params.subject,
            "priority": params.priority,
        },
        "error": None,
    }


send_email_tool = StructuredTool.from_function(
    name="send_email",
    description="发送邮件。适用于需要给指定邮箱发送通知/报告的场景。",
    func=_send_email,
    args_schema=EmailParams,
)
```

### 2.6 `tools/tool_integration.py`详解（已实现）

```python
【文件: tools/tool_integration.py】
【完整路径: D:\My\python\project\Langchain-demo\project\tools\tool_integration.py】

"""
工具与LLM集成
"""
import sys
from pathlib import Path

# 添加 project 目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain_community.chat_models.tongyi import ChatTongyi
from tools.basic_tools import safe_calculator, get_current_time, text_stats
from src.config import Config
from langchain_core.messages import HumanMessage, ToolMessage


def create_llm_with_tools():
    """创建带工具绑定的LLM"""
    llm = ChatTongyi(model_name="qwen-plus", dashscope_api_key=Config.OPENAI_API_KEY)
    tools = [safe_calculator, get_current_time, text_stats]
    llm_with_tools = llm.bind_tools(tools)
    return llm_with_tools, tools


def run_tool_call_loop(llm_with_tools, tools_list: list, user_question: str) -> str:
    """
    工具调用闭环实现

    流程：
    1. LLM生成tool_calls或直接回答
    2. 执行工具
    3. ToolMessage回填
    4. 循环直到无tool_calls
    """
    tools_by_name = {t.name: t for t in tools_list}
    messages = [HumanMessage(content=user_question)]

    while True:
        ai = llm_with_tools.invoke(messages)

        # 无tool_calls：直接回答
        if not getattr(ai, "tool_calls", None):
            return ai.content

        # 有tool_calls：执行并回填
        messages.append(ai)
        for call in ai.tool_calls:
            tool_name = call["name"]
            tool_args = call.get("args", {})
            tool = tools_by_name[tool_name]

            result = tool.invoke(tool_args)
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
```

### 2.7 `tools/demo_tool_loop.py`详解（已实现）

```python
【文件: tools/demo_tool_loop.py】
【完整路径: D:\My\python\project\Langchain-demo\project\tools\demo_tool_loop.py】

"""
工具调用闭环演示
运行方式: python tools/demo_tool_loop.py
"""
import sys
from pathlib import Path

# 添加 project 目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.tool_integration import create_llm_with_tools, run_tool_call_loop


def main():
    llm_with_tools, tools = create_llm_with_tools()

    question = "帮我计算 (1+2)**3，然后统计'你好 world'的英文单词数"

    result = run_tool_call_loop(llm_with_tools, tools, question)
    print(f"最终回答: {result}")


if __name__ == "__main__":
    main()
```

---

## 3. 工具开发规范

### 3.1 一个高质量工具必须回答 5 个问题

| 问题 | 对应代码位置 | 示例 |
|------|-------------|------|
| 工具叫什么 | `@tool` 装饰器后的函数名 | `tools/basic_tools.py: safe_calculator` |
| 工具能做什么 | 函数 docstring | `safe_calculator` 的 docstring |
| 需要哪些参数 | 参数类型注解 | `expression: str` |
| 返回什么 | 返回类型注解 + 返回值 | `-> dict` + `{"ok":..., "data":..., "error":...}` |
| 失败怎么办 | try-except + 错误返回 | `except Exception as e: return {"ok": False,...}` |

### 3.2 推荐的返回格式

```python
# 成功返回格式
return {"ok": True, "data": {...}, "error": None}

# 失败返回格式
return {"ok": False, "data": None, "error": "可行动的错误信息"}
```

### 3.3 安全原则

| 原则 | 实现位置 | 说明 |
|------|----------|------|
| 工具必须可控 | `tools/basic_tools.py:_safe_eval` | AST白名单解析 |
| 工具必须有超时 | 待实现 | API工具需要timeout |
| 工具必须可解释失败 | `tools/basic_tools.py:safe_calculator` | 返回可行动建议 |

---

## 4. 阶段 1：基础工具开发

### 4.1 工具开发流程

```
步骤1: 定义工具函数        → 文件: tools/basic_tools.py
步骤2: 添加@tool装饰器     → 文件: tools/basic_tools.py
步骤3: 编写docstring       → 文件: tools/basic_tools.py
步骤4: 导出工具            → 文件: tools/__init__.py
步骤5: 编写测试            → 文件: tests/test_tools.py
```

### 4.2 已完成的基础工具

| 工具名称 | 文件位置 | 状态 |
|----------|----------|------|
| `safe_calculator` | `tools/basic_tools.py` | ✅ |
| `get_current_time` | `tools/basic_tools.py` | ✅ |
| `text_stats` | `tools/basic_tools.py` | ✅ |
| `unit_convert` | `tools/basic_tools.py` | ✅ |

---

## 5. 阶段 2：结构化参数工具

### 5.1 已完成的参数模型

```python
【文件: tools/schemas.py】
已实现的模型：
- EmailParams: 邮件发送参数
- RAGQAParams: RAG问答参数
```

### 5.2 已完成的高级工具

```python
【文件: tools/advanced_tools.py】
已实现的工具：
- send_email_tool: 邮件发送工具（使用EmailParams）
```

### 5.3 待添加的高级工具示例：RAG 问答工具（可选扩展）

> 说明：你当前项目已有 `src/rag_chain.py`，这个示例把它封装成“工具”，后续 Agent 就能主动调用 RAG。

```python
from langchain_core.tools import StructuredTool
from src.rag_chain import RAGChain
from src.vectorstore import VectorStoreManager
from src.config import Config
from tools.schemas import RAGQAParams


def _rag_qa(params: RAGQAParams) -> dict:
    """RAG问答实现"""
    try:
        manager = VectorStoreManager(
            persist_directory=Config.VECTOR_DB_PATH,
            api_key=Config.OPENAI_API_KEY,
            embedding_model=Config.EMBEDDING_MODEL
        )
        retriever = manager.get_retriever(top_k=params.top_k)

        rag_chain = RAGChain(
            retriever=retriever,
            model_name=Config.LLM_MODEL,
            api_key=Config.OPENAI_API_KEY,
        )

        answer = rag_chain.invoke(params.question)
        return {"ok": True, "data": {"answer": answer}, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "error": f"问答失败: {e}"}


rag_qa_tool = StructuredTool.from_function(
    name="rag_qa",
    description="知识库问答工具。从环保知识库中检索答案。",
    func=_rag_qa,
    args_schema=RAGQAParams,
)
```

---

## 6. 阶段 3：LLM 工具调用闭环

### 6.1 你需要理解的“闭环”是什么意思

闭环就是一圈完整流程：

1. 用户提问  
2. LLM 决定要不要调用工具（生成 `tool_calls`）  
3. 你的代码真正执行工具  
4. 把工具结果用 `ToolMessage` 回填给 LLM  
5. LLM 基于工具结果生成最终答案（或继续下一轮工具调用）

### 6.2 代码位置

- 绑定工具：`tools/tool_integration.py -> create_llm_with_tools()`  
- 闭环循环：`tools/tool_integration.py -> run_tool_call_loop()`  
- 演示脚本：`tools/demo_tool_loop.py`

---

## 7. 阶段 4：Agent 集成（LangChain 1.0+）

> 重要：你在 LangChain 1.0+ 环境中运行时，旧的 `AgentExecutor` 可能无法导入。  
> 新版推荐用 `create_agent`（底层基于 LangGraph 图运行时）。

### 7.1 旧参数怎么迁移（你关心的 max_iterations 等）

旧写法（`AgentExecutor`）常见控制项：

- `max_iterations=6`：最多循环 6 轮（防止死循环）
- `return_intermediate_steps=True`：返回中间步骤（看工具调用过程）
- `handle_parsing_errors=True`：解析/格式错误时尽量自愈
- `verbose=True`：打印详细过程

在 LangChain 1.0+ 的 `create_agent` 中：

1) **max_iterations → recursion_limit**（运行配置里控制步数）

```python
result = agent.invoke(
    {"messages": [HumanMessage(content=question)]},
    {"recursion_limit": 6},
)
```

2) **return_intermediate_steps → 直接看 result["messages"]**  
`result["messages"]` 就是完整过程回放（含工具请求与工具结果）。

3) **handle_parsing_errors → 用 middleware 统一兜底工具错误（推荐）**  
新架构更推荐把错误处理放进 middleware，让错误变成 ToolMessage 回给模型，让模型重试/换策略。

4) **verbose → debug / stream**  
你可以打印 `result["messages"]`，或用 `agent.stream(..., stream_mode="updates")` 逐步查看节点更新。

### 7.2 创建 Agent 实现文件：`src/agent.py`

```python
【文件: src/agent.py】

"""
Agent实现（LangChain 1.0+ 推荐写法）
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_community.chat_models.tongyi import ChatTongyi

from tools import safe_calculator, get_current_time, text_stats, unit_convert
from src.config import Config


def create_environment_agent():
    """创建环境小助手Agent（LangChain 1.0+）"""

    # 1) LLM配置
    llm = ChatTongyi(
        model_name="qwen-plus",
        dashscope_api_key=Config.OPENAI_API_KEY,
    )

    # 2) 工具列表
    tools = [safe_calculator, get_current_time, text_stats, unit_convert]

    # 3) 系统提示词（规则）
    system_prompt = (
        "你是环境小助手。遇到计算/统计/时间/单位转换问题必须调用对应工具。"
        "工具结果为准，不要编造。不确定的信息要说不知道。"
    )

    # 4) 创建Agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )

    return agent


def run_agent(question: str, recursion_limit: int = 6) -> dict:
    """运行Agent，并限制最大步数"""
    agent = create_environment_agent()
    return agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        {"recursion_limit": recursion_limit},
    )
```

### 7.3 创建 Agent 演示脚本：`demo_agent.py`

```python
【文件: demo_agent.py】

"""
Agent演示脚本（LangChain 1.0+）
运行方式: python demo_agent.py
"""

from src.agent import run_agent


def main():
    question = "帮我算 (1+2)**3，统计'你好 world'的英文单词数，最后告诉我现在时间。"
    result = run_agent(question, recursion_limit=6)

    print("=" * 50)
    print("最终回答:")
    print(result["messages"][-1].content)
    print("=" * 50)

    print("过程回放（messages）:")
    for msg in result["messages"]:
        print(f"[{msg.__class__.__name__}] {getattr(msg, 'content', '')}")


if __name__ == "__main__":
    main()
```

---

## 8. 与现有 RAG 项目集成

### 8.1 现有 RAG 文件位置

| 文件 | 位置 | 功能 |
|------|------|------|
| 配置管理 | `src/config.py` | API密钥、模型配置 |
| 文档处理 | `src/document_processor.py` | 文档加载、分块 |
| 向量存储 | `src/vectorstore.py` | Chroma管理 |
| RAG链 | `src/rag_chain.py` | 问答链实现 |
| Web应用 | `app.py` | Flask服务 |
| 命令行入口 | `main.py` | CLI交互 |
| 对话式RAG | `advanced/conversational_rag.py` | 带记忆的RAG |
| 混合检索 | `advanced/hybrid_retriever.py` | BM25+向量检索 |
| 知识库文档 | `data/knowledge/*.txt` | 环保知识 |

### 8.2 Flask Web 应用 API 端点

现有API端点：
- GET  `/health`         - 健康检查  
- POST `/api/chat`       - 问答接口  
- POST `/api/chat/stream` - 流式问答  
- POST `/api/rebuild`    - 重建知识库  

### 8.3 创建 RAG 工具文件（可选）：`tools/rag_tools.py`

```python
"""
RAG相关工具
"""

from langchain_core.tools import tool
from src.rag_chain import RAGChain
from src.vectorstore import VectorStoreManager
from src.config import Config
import threading
import time
import os


# 执行锁（防止并发重建）
_rebuild_lock = threading.Lock()


@tool
def rag_qa(question: str) -> dict:
    """
    知识库问答工具。从环保知识库中检索答案。
    """
    try:
        manager = VectorStoreManager(
            persist_directory=Config.VECTOR_DB_PATH,
            api_key=Config.OPENAI_API_KEY,
            embedding_model=Config.EMBEDDING_MODEL
        )
        retriever = manager.get_retriever(top_k=Config.RETRIEVE_TOP_K)

        rag_chain = RAGChain(
            retriever=retriever,
            model_name=Config.LLM_MODEL,
            api_key=Config.OPENAI_API_KEY,
        )

        docs = rag_chain.get_retrieved_docs(question)
        answer = rag_chain.invoke(question)

        return {
            "ok": True,
            "data": {
                "answer": answer,
                "sources": [doc.metadata.get("source", "") for doc in docs]
            },
            "error": None
        }
    except Exception as e:
        return {"ok": False, "data": None, "error": f"问答失败: {e}"}


@tool
def rag_rebuild(confirm: bool = False) -> dict:
    """
    知识库重建工具。重新加载所有知识文档。

    注意：这是高成本操作，需要用户确认。
    """
    if not confirm:
        return {"ok": False, "data": None, "error": "这是高成本操作，请传入 confirm=True 确认执行。"}

    if not _rebuild_lock.acquire(blocking=False):
        return {"ok": False, "data": None, "error": "知识库正在重建中，请稍后再试"}

    try:
        start_time = time.time()

        from src.document_processor import DocumentProcessor
        processor = DocumentProcessor(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        chunks = processor.process(Config.KNOWLEDGE_PATH)

        manager = VectorStoreManager(
            persist_directory=Config.VECTOR_DB_PATH,
            api_key=Config.OPENAI_API_KEY,
            embedding_model=Config.EMBEDDING_MODEL
        )
        manager.create_from_documents(chunks)

        elapsed = time.time() - start_time
        return {
            "ok": True,
            "data": {"elapsed_seconds": elapsed, "chunks": len(chunks), "message": "知识库重建完成"},
            "error": None
        }
    except Exception as e:
        return {"ok": False, "data": None, "error": f"重建失败: {e}"}
    finally:
        _rebuild_lock.release()


@tool
def system_health() -> dict:
    """
    系统健康检查工具。
    """
    try:
        status = {
            "api_key_set": bool(Config.OPENAI_API_KEY),
            "knowledge_dir_exists": os.path.exists(Config.KNOWLEDGE_PATH),
            "chroma_db_exists": os.path.exists(Config.VECTOR_DB_PATH),
        }

        all_ok = all(status.values())
        return {"ok": all_ok, "data": status, "error": None if all_ok else "部分组件异常"}
    except Exception as e:
        return {"ok": False, "data": None, "error": f"检查失败: {e}"}
```

### 8.4 更新工具导出（可选）

```python
from .basic_tools import safe_calculator, get_current_time, text_stats, unit_convert
from .rag_tools import rag_qa, rag_rebuild, system_health

ALL_TOOLS = [
    safe_calculator,
    get_current_time,
    text_stats,
    unit_convert,
    rag_qa,
    rag_rebuild,
    system_health,
]
```

---

## 9. 调试与测试（重要更新）

### 9.1 创建测试文件：`tests/test_tools.py`

```python
"""
工具单元测试
运行方式: pytest tests/test_tools.py -v
"""

import pytest
from tools.basic_tools import safe_calculator, get_current_time, text_stats, unit_convert


class TestSafeCalculator:
    """安全计算器测试"""

    def test_basic_addition(self):
        """测试加法"""
        result = safe_calculator.invoke({"expression": "1+2"})
        assert result["ok"] is True
        assert result["data"]["value"] == 3.0

    def test_complex_expression(self):
        """测试复杂表达式"""
        result = safe_calculator.invoke({"expression": "(1+2)**3"})
        assert result["ok"] is True
        assert result["data"]["value"] == 27.0

    def test_invalid_expression(self):
        """测试无效表达式"""
        result = safe_calculator.invoke({"expression": "abc"})
        assert result["ok"] is False
        assert "error" in result


class TestGetCurrentTime:
    """时间工具测试"""

    def test_default_format(self):
        """测试默认格式"""
        result = get_current_time.invoke({})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_custom_format(self):
        """测试自定义格式"""
        result = get_current_time.invoke({"format_str": "%Y-%m-%d"})
        assert isinstance(result, str)


class TestTextStats:
    """文本统计测试"""

    def test_chinese_text(self):
        """测试中文文本"""
        result = text_stats.invoke({"text": "你好世界"})
        assert result["ok"] is True
        assert result["data"]["chinese_chars"] == 4

    def test_mixed_text(self):
        """测试混合文本"""
        result = text_stats.invoke({"text": "你好 world"})
        assert result["ok"] is True
        assert result["data"]["chinese_chars"] == 2
        assert result["data"]["english_words"] == 1


class TestUnitConvert:
    """单位转换测试"""

    def test_celsius_to_fahrenheit(self):
        """测试摄氏度转华氏度"""
        result = unit_convert.invoke({"value": 0, "from_unit": "C", "to_unit": "F"})
        assert result["ok"] is True
        assert result["data"]["value"] == 32.0

    def test_km_to_miles(self):
        """测试公里转英里"""
        result = unit_convert.invoke({"value": 1, "from_unit": "km", "to_unit": "miles"})
        assert result["ok"] is True
        assert abs(result["data"]["value"] - 0.621371) < 0.001

    def test_invalid_conversion(self):
        """测试无效转换"""
        result = unit_convert.invoke({"value": 100, "from_unit": "kg", "to_unit": "lb"})
        assert result["ok"] is False
```

### 9.2 推荐运行命令

基础运行（更清晰的输出）：

```bash
pytest -v
```

只跑安全计算器相关测试（你这次用来验证修复的命令）：

```bash
pytest tests/test_tools.py::TestSafeCalculator -q
```

### 9.3 pytest 常见坑：默认 addopts 带 --cov 导致报错

**现象**：

```
pytest: error: unrecognized arguments: --cov=src --cov-report=term-missing
```

**原因**：  
`pyproject.toml` 里 pytest 默认参数 `addopts` 带了 `--cov...`，但当前环境没有安装 `pytest-cov` 插件。

**解决方案（推荐两选一）**：

1) **只想先跑通测试（推荐新手）**：把 `addopts` 改成 `-v`  
2) **想要 coverage 报告**：安装 `pytest-cov`，然后再加回 `--cov...`

---

## 10. 练习清单

按顺序完成以下练习：

| # | 练习内容 | 文件位置 | 状态 |
|---|----------|----------|------|
| 1 | 修复 `__init__.py` 工具导出名称 | `tools/__init__.py` | ✅ 已完成 |
| 2 | 添加 `unit_convert` 单位转换工具 | `tools/basic_tools.py` | ✅ 已完成 |
| 3 | 创建 `schemas.py` 参数模型 | `tools/schemas.py` | ✅ 已完成 |
| 4 | 创建 `advanced_tools.py` 高级工具 | `tools/advanced_tools.py` | ✅ 已完成 |
| 5 | 创建 `tool_integration.py` | `tools/tool_integration.py` | ✅ 已完成 |
| 6 | 创建 `demo_tool_loop.py` 演示脚本 | `tools/demo_tool_loop.py` | ✅ 已完成 |
| 7 | 创建 `agent.py` Agent实现（LangChain 1.0+） | `src/agent.py` | ✅（按本文实现） |
| 8 | 创建 `demo_agent.py` Agent演示（LangChain 1.0+） | `demo_agent.py` | ✅（按本文实现） |
| 9 | 创建 `rag_tools.py` RAG工具 | `tools/rag_tools.py` | ⬜ 可选 |
| 10 | 创建 `test_tools.py` 测试 | `tests/test_tools.py` | ⬜ 建议完成 |
| 11 | 实现 `tool_manager.py` 工具管理器 | `tools/tool_manager.py` | ⬜ 可选 |
| 12 | 实现 `api_tools.py` API工具 | `tools/api_tools.py` | ⬜ 可选 |

---

## 11. 附录：关键配置文件与兼容说明

### 11.1 环境变量文件（示例）

```
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-turbo
EMBEDDING_MODEL=text-embedding-v3
```

### 11.2 pyproject.toml（pytest 配置建议｜重要）

如果你不想因为缺少插件而导致 pytest 报错，建议用安全默认值：

```toml
[tool.pytest.ini_options]
addopts = "-v"
```

如果你确实需要 coverage（可选）：

1. 安装插件：`pip install pytest-cov`
2. 再把 addopts 改成：

```toml
[tool.pytest.ini_options]
addopts = "-v --cov=src --cov-report=term-missing"
```

### 11.3 LangChain 0.3.x 兼容说明（如果你不升级）

如果你的环境还是 0.3.x，下面两种都可行：

1) **继续使用旧写法**：`AgentExecutor + create_tool_calling_agent`（你老文档那套）  
2) **升级到 1.0+ 并使用本文的 create_agent 写法**（推荐）

> 如果你坚持使用 LangChain 1.0+ 但又想继续旧 API：通常需要安装 `langchain-classic`（兼容包）。  
> 但既然你已经开始迁移到新写法，建议直接用本文的 `create_agent + recursion_limit + messages 回放` 的方式。

