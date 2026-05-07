# LangChain 高级 Agent 开发指南

> **目标**：学完后你能将基础 Agent 升级为具备记忆、自我反思、多工具协同、流式输出等能力的高级 Agent。
>
> **适用项目背景**：基于深度学习的宜春市环境检测数据分析可视化项目。

---

TODO

1.优化固定json格式输出的方法：**思路解析：** 考察真正的 Agent 工程经验。纸上谈兵的人只会说“在提示词里加一句只输出JSON”，做过项目的人才知道模型根本不可控。

**具体方案：**

- **正则提取与清理：** 在 Java 端解析前，不要直接反序列化。先用正则表达式（如提取 `\{.*\}` 之间的内容）把多余的 Markdown 标记（如 ```json ）和问候语剥离掉。
- **LangChain 的 OutputParser（重试机制）：** 提到 LangChain/LangChain4j 内部的 `OutputFixingParser` 或 `RetryOutputParser`。当第一次 JSON 解析失败（抛出异常）时，捕获该异常，并将**报错信息连同刚才生成的错误文本**一起再次喂给大模型，让它“修复自己的格式错误”。
- **Function Calling (Tools)：** 最底层的解决方案是强制使用 OpenAI 或主流模型提供的 Function Calling 接口，而不是仅仅靠系统提示词约束，这样模型会在底层输出结构化的参数对象，大幅降低格式错误率。
- Langchian的方法：pydantic利用这个定义输出结构

2.解析反思结果的完整版





## 更新记录（2026-04-13）

本文档基于现有项目代码编写，所有代码位置均已标明。
已验证文件存在性和实际行数。

---

## 项目现状分析

### 当前 Agent 能力评估

| 能力维度 | 当前状态 | 文件位置 | 实际状态 | 评级 |
|----------|----------|----------|----------|------|
| 工具调用 | ✅ 已实现 | `src/agent.py` | 存在且已实现（56行） | 基础级 |
| 多工具支持 | ✅ 已实现 | `tools/basic_tools.py` | 存在且已实现 | 基础级 |
| RAG工具 | ✅ 已实现 | `tools/rag_tools.py` | 存在且已实现 | 基础级 |
| 高级Agent | ⚠️ 文件存在但未实现 | `src/advanced_agent.py` | 存在但为空 | 待实现 |
| API工具 | ⚠️ 文件存在但未实现 | `tools/api_tools.py` | 存在但为空 | 待实现 |
| 工具管理器 | ⚠️ 文件存在但未实现 | `tools/tool_manager.py` | 存在但为空 | 待实现 |
| 记忆系统 | ❌ 未实现 | - | 需在 `advanced_agent.py` 中实现 | 缺失 |
| 错误自愈 | ❌ 未实现 | - | 需新建 `tools/error_handling.py` | 缺失 |
| 自我反思 | ❌ 未实现 | - | 需新建 `src/reflection.py` | 缺失 |
| 流式输出 | ✅ 已实现 | `src/rag_chain.py:104-115` | 行数已验证 | 已有 |
| 递归限制 | ⚠️ 部分支持 | `src/agent.py` | 需增强 | 部分 |
| 状态管理 | ❌ 未实现 | - | 需新建 `src/state_manager.py` | 缺失 |

### 现有文件结构（实际状态）

```
【项目根目录: D:\My\python\project\Langchain-demo\project\】

├── src/
│   ├── agent.py              # ✅ 已实现（第1-56行）
│   ├── advanced_agent.py     # ⚠️ 文件存在但为空（待实现）
│   ├── config.py             # ✅ 已实现（第1-28行）
│   ├── rag_chain.py          # ✅ 已实现（流式输出第104-115行已验证）
│   ├── vectorstore.py        # ✅ 已实现
│   └── document_processor.py # ✅ 已实现
│
├── tools/
│   ├── basic_tools.py        # ✅ 已实现（第1-177行）
│   ├── advanced_tools.py     # ✅ 已实现（第1-27行）
│   ├── rag_tools.py          # ✅ 已实现（第1-158行）
│   ├── tool_integration.py   # ✅ 已实现（第1-87行）
│   ├── schemas.py            # ✅ 已实现
│   ├── api_tools.py          # ⚠️ 文件存在但为空（待实现）
│   └── tool_manager.py       # ⚠️ 文件存在但为空（待实现）
│
├── tests/
│   └── test_tools.py         # ✅ 已实现（第1-84行）
│
├── demo_agent.py             # ✅ 已实现（第1-25行）
└── app.py                    # ✅ Flask Web应用已实现
```

---

## 目录

1. [高级 Agent 基础知识](#1-高级-agent-基础知识)
2. [阶段一：增强记忆系统](#2-阶段一增强记忆系统)
3. [阶段二：递归限制与错误处理](#3-阶段二递归限制与错误处理)
4. [阶段三：自我反思机制](#4-阶段三自我反思机制)
5. [阶段四：多工具协同与工具链](#5-阶段四多工具协同与工具链)
6. [阶段五：流式输出与状态管理](#6-阶段五流式输出与状态管理)
7. [阶段六：完整高级 Agent 实现](#7-阶段六完整高级-agent-实现)
8. [阶段七：工具验证与安全增强](#8-阶段七工具验证与安全增强)
9. [练习清单](#9-练习清单)
10. [附录：配置文件](#10-附录配置文件)

---

## 1. 高级 Agent 基础知识

### 1.1 什么是高级 Agent？

**基础 Agent**：能调用工具，但不具备以下能力：
- 无法记住上下文
- 遇到错误直接崩溃
- 无法自我修正
- 单步执行，无规划

**高级 Agent**：具备以下核心能力：

| 能力 | 说明 | 为什么重要 |
|------|------|------------|
| **记忆系统** | 保存对话历史，理解上下文 | 多轮对话连贯性 |
| **递归限制** | 防止无限循环 | 安全性、成本控制 |
| **错误自愈** | 工具失败时自动重试或换策略 | 稳定性 |
| **自我反思** | 评估自己的回答质量 | 准确性提升 |
| **工具链** | 多工具按顺序/条件执行 | 复杂任务处理 |
| **流式输出** | 实时返回中间结果 | 用户体验 |
| **状态管理** | 保存Agent执行状态 | 可恢复、可调试 |

### 1.2 LangChain 1.0+ 高级 Agent 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Advanced Agent Architecture               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│   │   Input      │───▶│   Memory     │───▶│   Planner    │  │
│   │  (Question)  │    │  (History)   │    │  (Strategy)  │  │
│   └──────────────┘    └──────────────┘    └──────────────┘  │
│                                              │               │
│                                              ▼               │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│   │   Output     │◀───│   Reflector  │◀───│   Executor   │  │
│   │  (Answer)    │    │  (Evaluate)  │    │  (Tools)     │  │
│   └──────────────┘    └──────────────┘    └──────────────┘  │
│                                              │               │
│                                              ▼               │
│                        ┌──────────────────────────────────┐  │
│                        │       Error Handler              │  │
│                        │   (Retry / Fallback / Report)    │  │
│                        └──────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 核心依赖升级清单

```bash
# 确保安装以下依赖（在 pyproject.toml 或 requirements.txt）
pip install langchain>=0.3.0
pip install langchain-community>=0.3.0
pip install langchain-core>=0.3.0
pip install langgraph>=0.2.0  # 高级Agent核心
pip install pydantic>=2.0
```

---

## 2. 阶段一：增强记忆系统

### 2.1 为什么需要记忆？

**当前问题**：

```python
【文件: src/agent.py】
【行数: 30-39】

def run_agent(question:str)->dict:
    executor = create_environment_agent()
    return executor.invoke({"messages":[HumanMessage(content=question)]})
```

每次调用都是全新对话，Agent 无法记住之前的内容。

**期望效果**：
```
用户：帮我计算 (1+2)**3
Agent：结果是 27
用户：刚才的结果是多少？
Agent：刚才的计算结果是 27（能记住上下文）
```

### 2.2 记忆系统类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **ConversationBufferMemory** | 保存所有历史 | 短对话 |
| **ConversationBufferWindowMemory** | 只保存最近N轮 | 长对话 |
| **ConversationSummaryMemory** | 自动总结历史 | 超长对话 |
| **VectorStoreMemory** | 向量检索历史 | 知识型对话 |

### 2.3 实现方案：使用 LangGraph State

LangChain 1.0+ 推荐**在 State 中保存 messages**，而不是单独的 Memory 类。

```python
【文件: src/advanced_agent.py】
【说明: 文件已存在但为空，需添加以下代码实现】

"""
高级Agent实现 - 记忆系统增强
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_models.tongyi import ChatTongyi
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from tools import safe_calculator, get_current_time, text_stats, unit_convert
from tools.rag_tools import rag_qa, system_health
from src.config import Config


# ========== 状态定义（记忆核心） ==========

class AgentState(BaseModel):
    """Agent状态模型 - 包含对话历史"""
    messages: List[Dict[str, Any]] = []  # 对话历史
    current_question: str = ""           # 当前问题
    tool_calls: List[Dict] = []          # 工具调用记录
    reflection_result: Optional[str] = None  # 自我反思结果
    error_count: int = 0                 # 错误计数
    max_iterations: int = 6              # 最大迭代次数
    iteration_count: int = 0             # 当前迭代次数


class MemoryManager:
    """
    记忆管理器

    功能：
    1. 保存对话历史
    2. 提取最近N轮对话
    3. 清空历史
    """

    def __init__(self, max_history: int = 10):
        """
        初始化记忆管理器

        Args:
            max_history: 保存的最大对话轮数
        """
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.history.append({"role": role, "content": content})
        # 超过限制时移除最早的
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-(self.max_history * 2):]

    def get_history(self) -> List[Dict]:
        """获取完整历史"""
        return self.history

    def get_recent(self, n: int = 3) -> List[Dict]:
        """获取最近n轮对话"""
        return self.history[-(n * 2):]

    def clear(self):
        """清空历史"""
        self.history = []

    def format_for_llm(self) -> str:
        """格式化历史供LLM使用"""
        formatted = []
        for msg in self.history:
            role = msg["role"]
            content = msg["content"]
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)


# ========== 带记忆的Agent ==========

class AdvancedAgent:
    """
    高级Agent类

    核心能力：
    1. 对话记忆
    2. 递归限制
    3. 错误处理
    """

    def __init__(self, max_history: int = 10, max_iterations: int = 6):
        """
        初始化高级Agent

        Args:
            max_history: 最大保存对话轮数
            max_iterations: 最大工具调用迭代次数
        """
        self.memory = MemoryManager(max_history=max_history)
        self.max_iterations = max_iterations

        # LLM配置
        self.llm = ChatTongyi(
            model_name="qwen-plus",
            dashscope_api_key=Config.OPENAI_API_KEY,
        )

        # 工具列表（整合所有工具）
        self.tools = [
            safe_calculator,
            get_current_time,
            text_stats,
            unit_convert,
            rag_qa,
            system_health,
        ]

        # 系统提示词（增强版）
        self.system_prompt = """
你是高级环境助手，具备以下能力：
1. 计算与统计（使用safe_calculator, text_stats）
2. 单位转换（使用unit_convert）
3. 知识库问答（使用rag_qa）
4. 系统检查（使用system_health）

工作原则：
- 遇到计算问题必须调用工具，不要自行计算
- 知识问题优先使用rag_qa检索知识库
- 不确定的信息要说明"不确定"，不要编造
- 工具失败时要分析原因并重试或换策略
"""

    def chat(self, question: str) -> Dict[str, Any]:
        """
        带记忆的对话

        Args:
            question: 用户问题

        Returns:
            包含回答和执行信息的字典
        """
        # 1. 保存用户问题到记忆
        self.memory.add_message("user", question)

        # 2. 构建完整消息（历史 + 当前问题）
        history_context = self.memory.format_for_llm()
        full_prompt = f"""
对话历史：
{history_context}

当前问题：{question}

请根据对话历史回答当前问题，如果问题与之前对话相关，请引用之前的上下文。
"""

        # 3. 创建Agent并执行
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

        # 4. 执行并限制迭代次数
        result = agent.invoke(
            {"messages": [HumanMessage(content=full_prompt)]},
            {"recursion_limit": self.max_iterations},
        )

        # 5. 提取回答
        answer = result["messages"][-1].content

        # 6. 保存回答到记忆
        self.memory.add_message("assistant", answer)

        # 7. 返回结果
        return {
            "answer": answer,
            "history": self.memory.get_history(),
            "tool_calls": self._extract_tool_calls(result),
        }

    def _extract_tool_calls(self, result: Dict) -> List[Dict]:
        """提取工具调用记录"""
        tool_calls = []
        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for call in msg.tool_calls:
                    tool_calls.append({
                        "tool": call.get("name"),
                        "args": call.get("args"),
                    })
        return tool_calls

    def reset(self):
        """重置Agent状态"""
        self.memory.clear()
```

### 2.4 创建演示脚本

```python
【文件: demo_advanced_agent.py】（需新建）

"""
高级Agent演示脚本（带记忆）
运行方式: python demo_advanced_agent.py
"""

from src.advanced_agent import AdvancedAgent


def demo_memory():
    """演示记忆功能"""
    agent = AdvancedAgent(max_history=5, max_iterations=6)

    print("=" * 60)
    print("高级Agent记忆功能演示")
    print("=" * 60)

    # 第一轮对话
    print("\n【第一轮】")
    question1 = "帮我计算 (1+2)**3"
    result1 = agent.chat(question1)
    print(f"问题: {question1}")
    print(f"回答: {result1['answer']}")
    print(f"工具调用: {result1['tool_calls']}")

    # 第二轮对话（测试记忆）
    print("\n【第二轮】")
    question2 = "刚才的计算结果是多少？"
    result2 = agent.chat(question2)
    print(f"问题: {question2}")
    print(f"回答: {result2['answer']}")
    print(f"（Agent能记住之前的计算结果）")

    # 第三轮对话
    print("\n【第三轮】")
    question3 = "统计'你好世界'的字符数"
    result3 = agent.chat(question3)
    print(f"问题: {question3}")
    print(f"回答: {result3['answer']}")

    # 显示完整历史
    print("\n【对话历史】")
    for msg in result3['history']:
        print(f"[{msg['role']}]: {msg['content'][:50]}...")


def main():
    demo_memory()


if __name__ == "__main__":
    main()
```

---

## 3. 阶段二：递归限制与错误处理

### 3.1 递归限制的重要性

**问题场景**：Agent可能陷入无限循环
```
用户：查询天气
Agent：调用weather_tool
工具：失败（API错误）
Agent：调用weather_tool（重试）
工具：失败
Agent：调用weather_tool（继续重试）
... 无限循环 ...
```

### 3.2 递归限制实现

```python
【文件: src/advanced_agent.py】
【在AdvancedAgent类中添加】

    def chat_with_retry(self, question: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        带错误重试的对话

        Args:
            question: 用户问题
            max_retries: 每个工具的最大重试次数

        Returns:
            包含回答和错误信息的字典
        """
        self.memory.add_message("user", question)

        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                # 构建完整提示
                history_context = self.memory.format_for_llm()

                # 如果之前有错误，加入错误提示
                error_hint = ""
                if last_error:
                    error_hint = f"""
注意：上一次执行出现错误：{last_error}
请尝试不同的方法或工具来解决这个问题。
"""

                full_prompt = f"""
对话历史：
{history_context}
{error_hint}

当前问题：{question}
"""

                agent = create_agent(
                    model=self.llm,
                    tools=self.tools,
                    system_prompt=self.system_prompt,
                )

                result = agent.invoke(
                    {"messages": [HumanMessage(content=full_prompt)]},
                    {"recursion_limit": self.max_iterations},
                )

                answer = result["messages"][-1].content
                self.memory.add_message("assistant", answer)

                return {
                    "answer": answer,
                    "success": True,
                    "retry_count": retry_count,
                    "history": self.memory.get_history(),
                }

            except Exception as e:
                retry_count += 1
                last_error = str(e)

                # 记录错误到记忆
                self.memory.add_message("system", f"执行错误：{e}（重试 {retry_count}/{max_retries}）")

        # 所有重试都失败
        return {
            "answer": "抱歉，多次尝试后仍无法完成您的请求。",
            "success": False,
            "error": last_error,
            "retry_count": retry_count,
        }
```

### 3.3 工具级别错误处理

```python
【文件: tools/error_handling.py】（需新建）

"""
工具错误处理模块
"""

from typing import Dict, Any, Callable, Optional
from functools import wraps
import time


class ToolErrorHandler:
    """
    工具错误处理器

    功能：
    1. 自动重试
    2. 超时控制
    3. 错误报告
    """

    def __init__(
        self,
        max_retries: int = 3,
        timeout: float = 30.0,
        retry_delay: float = 1.0,
    ):
        """
        初始化错误处理器

        Args:
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
            retry_delay: 重试间隔（秒）
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_delay = retry_delay

    def wrap_tool(self, tool_func: Callable) -> Callable:
        """
        包装工具函数，添加错误处理

        Args:
            tool_func: 原工具函数

        Returns:
            包装后的函数
        """
        @wraps(tool_func)
        def wrapped(*args, **kwargs) -> Dict[str, Any]:
            retries = 0
            last_error = None

            while retries < self.max_retries:
                try:
                    # 执行工具
                    start_time = time.time()
                    result = tool_func(*args, **kwargs)
                    elapsed = time.time() - start_time

                    # 检查超时
                    if elapsed > self.timeout:
                        return {
                            "ok": False,
                            "data": None,
                            "error": f"工具执行超时（{elapsed:.1f}s > {self.timeout}s）",
                            "elapsed": elapsed,
                        }

                    return result

                except Exception as e:
                    retries += 1
                    last_error = str(e)

                    if retries < self.max_retries:
                        time.sleep(self.retry_delay)

            return {
                "ok": False,
                "data": None,
                "error": f"工具执行失败（{retries}次重试后）：{last_error}",
                "retries": retries,
            }

        return wrapped


# 使用示例
error_handler = ToolErrorHandler(max_retries=3, timeout=30.0)

# 包装现有工具
from tools.basic_tools import safe_calculator, get_current_time

safe_calculator_with_retry = error_handler.wrap_tool(safe_calculator)
```

---

## 4. 阶段三：自我反思机制

### 4.1 什么是自我反思？

自我反思是让Agent在给出回答后，评估自己的回答质量，并决定是否需要修正。

```
流程：
1. Agent生成回答
2. Agent反思：回答是否准确？是否完整？是否需要补充？
3. 如果需要修正，重新调用工具或调整回答
4. 输出最终回答
```

### 4.2 反思提示词设计

```python
【文件: src/reflection.py】（需新建）

"""
Agent自我反思模块
"""

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

评估结果格式：
- 评分：1-5分（5分最佳）
- 问题：列出发现的任何问题
- 建议：如果需要修正，说明修正方向

输出JSON格式：
{
    "score": <1-5>,
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "needs_revision": true/false
}
"""
```

### 4.3 在Agent中集成反思

```python
【文件: src/advanced_agent.py】
【在AdvancedAgent类中添加反思方法】

    def chat_with_reflection(self, question: str) -> Dict[str, Any]:
        """
        带自我反思的对话

        Args:
            question: 用户问题

        Returns:
            包含回答和反思结果的字典
        """
        # 1. 首次回答
        initial_result = self.chat(question)
        initial_answer = initial_result["answer"]
        tool_calls = initial_result["tool_calls"]

        # 2. 反思评估
        reflection_prompt = f"""
原始问题：{question}
给出的回答：{initial_answer}
使用的工具：{tool_calls}

请评估这个回答的质量，并说明是否需要修正。
"""

        reflection_result = self.llm.invoke([
            {"role": "system", "content": REFLECTION_PROMPT},
            {"role": "user", "content": reflection_prompt},
        ])

        reflection_text = reflection_result.content

        # 3. 解析反思结果（简化版）
        needs_revision = "needs_revision: true" in reflection_text.lower() or "需要修正" in reflection_text

        # 4. 如果需要修正，重新执行
        final_answer = initial_answer
        if needs_revision and self.memory.history:
            # 提取修正建议
            revision_prompt = f"""
根据反思结果，请重新回答用户问题：

原始问题：{question}
初始回答：{initial_answer}
反思发现的问题：{reflection_text}

请修正回答中的问题，给出更准确的答案。
"""

            revision_result = self.chat(revision_prompt)
            final_answer = revision_result["answer"]

        return {
            "answer": final_answer,
            "initial_answer": initial_answer,
            "reflection": reflection_text,
            "needs_revision": needs_revision,
            "tool_calls": tool_calls,
            "history": self.memory.get_history(),
        }
```

---

## 5. 阶段四：多工具协同与工具链

### 5.1 什么是工具链？

工具链是指多个工具按特定顺序或条件组合执行。

**场景示例**：
```
用户：分析这篇文档的统计信息，然后发邮件给我

需要执行的工具链：
1. text_stats(text) -> 统计结果
2. send_email(to, subject, body=统计结果) -> 发送邮件
```

### 5.2 工具链编排器

```python
【文件: tools/tool_chain.py】（需新建）

"""
工具链编排模块
"""

from typing import List, Dict, Any, Callable
from pydantic import BaseModel


class ToolStep(BaseModel):
    """工具步骤定义"""
    tool_name: str
    args: Dict[str, Any] = {}
    depends_on: List[str] = []  # 依赖的前置工具
    condition: str = ""  # 执行条件（可选）


class ToolChain:
    """
    工具链编排器

    功能：
    1. 定义多工具执行顺序
    2. 处理工具间依赖
    3. 管理中间结果传递
    """

    def __init__(self, tools: Dict[str, Callable]):
        """
        初始化工具链

        Args:
            tools: 工具名称到函数的映射
        """
        self.tools = tools
        self.results: Dict[str, Any] = {}

    def execute(self, steps: List[ToolStep]) -> Dict[str, Any]:
        """
        执行工具链

        Args:
            steps: 工具步骤列表

        Returns:
            所有步骤的执行结果
        """
        self.results = {}

        for step in steps:
            # 检查依赖是否满足
            for dep in step.depends_on:
                if dep not in self.results:
                    return {
                        "ok": False,
                        "error": f"依赖未满足：{step.tool_name} 需要 {dep}",
                        "completed": list(self.results.keys()),
                    }

            # 构建参数（可能包含前置工具结果）
            args = step.args.copy()
            for dep in step.depends_on:
                # 将前置结果传入参数
                args[f"{dep}_result"] = self.results[dep]

            # 执行工具
            tool = self.tools.get(step.tool_name)
            if not tool:
                return {
                    "ok": False,
                    "error": f"工具不存在：{step.tool_name}",
                    "completed": list(self.results.keys()),
                }

            try:
                result = tool.invoke(args) if hasattr(tool, "invoke") else tool(**args)
                self.results[step.tool_name] = result
            except Exception as e:
                return {
                    "ok": False,
                    "error": f"工具执行失败：{step.tool_name} - {e}",
                    "completed": list(self.results.keys()),
                }

        return {
            "ok": True,
            "results": self.results,
            "completed": list(self.results.keys()),
        }


# 使用示例
from tools.basic_tools import text_stats, safe_calculator
from tools.advanced_tools import send_email_tool

# 定义工具链
chain = ToolChain({
    "text_stats": text_stats,
    "safe_calculator": safe_calculator,
    "send_email": send_email_tool,
})

# 定义步骤
steps = [
    ToolStep(tool_name="text_stats", args={"text": "你好世界"}),
    ToolStep(
        tool_name="safe_calculator",
        args={"expression": "2+3"},
        depends_on=["text_stats"],  # 依赖text_stats完成
    ),
]

# 执行
result = chain.execute(steps)
```

### 5.3 Agent中的工具链决策

```python
【文件: src/advanced_agent.py】
【添加工具链规划能力】

    def analyze_and_plan(self, question: str) -> List[Dict]:
        """
        分析问题并规划工具链

        Args:
            question: 用户问题

        Returns:
            工具执行计划
        """
        planning_prompt = f"""
用户问题：{question}

可用工具：
- safe_calculator: 数学计算
- text_stats: 文本统计
- unit_convert: 单位转换
- rag_qa: 知识库问答
- system_health: 系统检查

请分析问题，决定需要使用哪些工具，以及执行顺序。

输出格式（JSON）：
{
    "tools_needed": ["tool1", "tool2"],
    "execution_order": ["tool1", "tool2"],
    "reasoning": "为什么需要这些工具"
}
"""

        result = self.llm.invoke([
            {"role": "system", "content": "你是一个工具规划专家。"},
            {"role": "user", "content": planning_prompt},
        ])

        return result.content
```

---

## 6. 阶段五：流式输出与状态管理

### 6.1 现有流式输出分析

```python
【文件: src/rag_chain.py】
【行数: 104-115】

def stream(self,question:str):
    """
   流式输出问答

   Args:
       question: 用户问题

   Yields:
       回答片段
   """
    for chunk in self.chain.stream(question):
        yield chunk
```

这是RAG链的流式输出，Agent需要类似能力。

### 6.2 Agent流式输出实现

```python
【文件: src/advanced_agent.py】
【添加流式输出方法】

    def chat_stream(self, question: str):
        """
        流式对话输出

        Args:
            question: 用户问题

        Yields:
            回答片段和状态更新
        """
        self.memory.add_message("user", question)

        history_context = self.memory.format_for_llm()
        full_prompt = f"""
对话历史：
{history_context}

当前问题：{question}
"""

        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

        # 使用stream模式
        for event in agent.stream(
            {"messages": [HumanMessage(content=full_prompt)]},
            {"recursion_limit": self.max_iterations},
            stream_mode="updates",
        ):
            # 提取事件类型和内容
            if "agent" in event:
                # Agent思考/输出
                yield {
                    "type": "agent",
                    "content": event["agent"].get("content", ""),
                }
            elif "tool" in event:
                # 工具执行
                yield {
                    "type": "tool",
                    "tool_name": event["tool"].get("name", ""),
                    "result": event["tool"].get("result", ""),
                }
            elif "final" in event:
                # 最终回答
                answer = event["final"].get("content", "")
                self.memory.add_message("assistant", answer)
                yield {
                    "type": "final",
                    "content": answer,
                }
```

### 6.3 状态持久化

```python
【文件: src/state_manager.py】（需新建）

"""
Agent状态持久化管理
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class StateManager:
    """
    状态管理器

    功能：
    1. 保存Agent执行状态
    2. 恢复中断的执行
    3. 状态历史记录
    """

    def __init__(self, state_dir: str = "./agent_states"):
        """
        初始化状态管理器

        Args:
            state_dir: 状态存储目录
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_state(self, session_id: str, state: Dict[str, Any]) -> str:
        """
        保存状态

        Args:
            session_id: 会话ID
            state: 状态数据

        Returns:
            状态文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}_{timestamp}.json"
        filepath = self.state_dir / filename

        state["saved_at"] = timestamp
        state["session_id"] = session_id

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def load_state(self, filepath: str) -> Dict[str, Any]:
        """
        加载状态

        Args:
            filepath: 状态文件路径

        Returns:
            状态数据
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_latest_state(self, session_id: str) -> Dict[str, Any] | None:
        """
        获取指定会话的最新状态

        Args:
            session_id: 会话ID

        Returns:
            最新状态或None
        """
        files = list(self.state_dir.glob(f"{session_id}_*.json"))
        if not files:
            return None

        # 按时间戳排序，取最新的
        files.sort(reverse=True)
        return self.load_state(str(files[0]))

    def list_sessions(self) -> List[str]:
        """
        列出所有会话ID

        Returns:
            会话ID列表
        """
        files = list(self.state_dir.glob("*.json"))
        sessions = set()
        for f in files:
            # 从文件名提取session_id
            parts = f.stem.split("_")
            if len(parts) >= 1:
                sessions.add(parts[0])
        return list(sessions)
```

---

## 7. 阶段六：完整高级 Agent 实现

### 7.1 整合所有能力的完整实现

```python
【文件: src/complete_agent.py】（需新建）

"""
完整高级Agent实现

整合能力：
1. 对话记忆
2. 递归限制
3. 错误处理与重试
4. 自我反思
5. 工具链编排
6. 流式输出
7. 状态持久化
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_models.tongyi import ChatTongyi
from typing import List, Dict, Any, Optional, Generator
from pydantic import BaseModel
import json

from tools import safe_calculator, get_current_time, text_stats, unit_convert
from tools.rag_tools import rag_qa, system_health
from tools.advanced_tools import send_email_tool
from src.config import Config
from src.state_manager import StateManager
from tools.tool_chain import ToolChain, ToolStep


# ========== 状态模型 ==========

class CompleteAgentState(BaseModel):
    """完整Agent状态"""
    session_id: str = ""
    messages: List[Dict[str, Any]] = []
    tool_history: List[Dict] = []
    reflection_history: List[str] = []
    error_count: int = 0
    iteration_count: int = 0
    max_iterations: int = 6
    max_retries: int = 3
    max_history: int = 10


# ========== 完整Agent ==========

class CompleteAdvancedAgent:
    """
    完整高级Agent

    整合所有高级能力：
    - 记忆系统
    - 错误处理
    - 自我反思
    - 工具链
    - 流式输出
    - 状态持久化
    """

    def __init__(
        self,
        max_history: int = 10,
        max_iterations: int = 6,
        max_retries: int = 3,
        enable_reflection: bool = True,
        state_dir: str = "./agent_states",
    ):
        """
        初始化完整Agent

        Args:
            max_history: 最大保存对话轮数
            max_iterations: 最大工具调用迭代次数
            max_retries: 最大重试次数
            enable_reflection: 是否启用自我反思
            state_dir: 状态存储目录
        """
        self.state = CompleteAgentState(
            max_history=max_history,
            max_iterations=max_iterations,
            max_retries=max_retries,
        )
        self.enable_reflection = enable_reflection
        self.state_manager = StateManager(state_dir)

        # LLM配置
        self.llm = ChatTongyi(
            model_name="qwen-plus",
            dashscope_api_key=Config.OPENAI_API_KEY,
        )

        # 完整工具列表
        self.tools = [
            safe_calculator,
            get_current_time,
            text_stats,
            unit_convert,
            rag_qa,
            system_health,
            send_email_tool,
        ]

        # 工具映射
        self.tools_map = {t.name: t for t in self.tools}

        # 工具链编排器
        self.tool_chain = ToolChain(self.tools_map)

        # 高级系统提示词
        self.system_prompt = """
你是高级环境助手，具备以下能力：
1. 计算与统计（使用safe_calculator, text_stats）
2. 单位转换（使用unit_convert）
3. 知识库问答（使用rag_qa）
4. 系统检查（使用system_health）
5. 邮件通知（使用send_email）

工作原则：
- 遇到计算问题必须调用工具，不要自行计算
- 知识问题优先使用rag_qa检索知识库
- 多步骤任务需要规划工具链执行顺序
- 工具失败时分析原因并尝试替代方案
- 不确定的信息要说明"不确定"，不要编造
- 完成任务后简要总结执行过程

错误处理策略：
- 如果工具返回错误，尝试不同的参数或工具
- 如果多次失败，向用户说明情况并建议替代方案
"""

    def chat(self, question: str) -> Dict[str, Any]:
        """
        完整功能对话

        Args:
            question: 用户问题

        Returns:
            包含完整执行信息的字典
        """
        # 1. 保存用户消息
        self.state.messages.append({"role": "user", "content": question})

        # 2. 构建完整上下文
        history_context = self._format_history()

        # 3. 执行Agent
        result = self._execute_with_retry(question, history_context)

        # 4. 自我反思（如果启用）
        if self.enable_reflection:
            result = self._reflect_and_revise(question, result)

        # 5. 保存回答
        self.state.messages.append({"role": "assistant", "content": result["answer"]})

        # 6. 持久化状态
        self.state.session_id = self._generate_session_id()
        self.state_manager.save_state(self.state.session_id, self._get_state_dict())

        # 7. 返回完整结果
        return result

    def chat_stream(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """
        流式对话

        Args:
            question: 用户问题

        Yields:
            状态更新和回答片段
        """
        self.state.messages.append({"role": "user", "content": question})
        history_context = self._format_history()

        full_prompt = f"""
对话历史：
{history_context}

当前问题：{question}
"""

        # 开始执行
        yield {"type": "start", "message": "开始处理..."}

        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

        # 流式执行
        for event in agent.stream(
            {"messages": [HumanMessage(content=full_prompt)]},
            {"recursion_limit": self.state.max_iterations},
            stream_mode="updates",
        ):
            if "agent" in event:
                content = event["agent"].get("content", "")
                if content:
                    yield {"type": "thinking", "content": content}
            elif "tool" in event:
                tool_name = event["tool"].get("name", "")
                yield {"type": "tool_call", "tool": tool_name}
            elif "final" in event:
                answer = event["final"].get("content", "")
                yield {"type": "answer", "content": answer}

        yield {"type": "complete", "message": "处理完成"}

    def _execute_with_retry(self, question: str, context: str) -> Dict[str, Any]:
        """
        带重试的执行
        """
        retries = 0
        last_error = None

        while retries < self.state.max_retries:
            try:
                error_hint = ""
                if last_error:
                    error_hint = f"""
上次执行错误：{last_error}
请尝试不同策略。
"""

                full_prompt = f"""
{context}
{error_hint}

当前问题：{question}
"""

                agent = create_agent(
                    model=self.llm,
                    tools=self.tools,
                    system_prompt=self.system_prompt,
                )

                result = agent.invoke(
                    {"messages": [HumanMessage(content=full_prompt)]},
                    {"recursion_limit": self.state.max_iterations},
                )

                answer = result["messages"][-1].content

                # 提取工具调用
                tool_calls = self._extract_tool_calls(result)

                return {
                    "answer": answer,
                    "success": True,
                    "tool_calls": tool_calls,
                    "retry_count": retries,
                }

            except Exception as e:
                retries += 1
                last_error = str(e)
                self.state.error_count += 1

        return {
            "answer": "抱歉，多次尝试后仍无法完成请求。",
            "success": False,
            "error": last_error,
            "retry_count": retries,
        }

    def _reflect_and_revise(self, question: str, result: Dict) -> Dict:
        """
        反思并修正
        """
        reflection_prompt = f"""
问题：{question}
回答：{result["answer"]}
工具：{result.get("tool_calls", [])}

请评估回答质量，给出1-5分评分和建议。
"""

        reflection = self.llm.invoke([
            {"role": "system", "content": "你是质量评估专家。"},
            {"role": "user", "content": reflection_prompt},
        ])

        reflection_text = reflection.content
        self.state.reflection_history.append(reflection_text)

        # 简化判断：是否需要修正
        needs_revision = "需要修正" in reflection_text or "评分：<3" in reflection_text

        if needs_revision:
            revision_prompt = f"""
根据评估建议修正回答：
{reflection_text}

原始回答：{result["answer"]}
"""

            revision = self.chat(revision_prompt)
            result["answer"] = revision["answer"]
            result["revised"] = True

        result["reflection"] = reflection_text
        return result

    def _format_history(self) -> str:
        """格式化历史"""
        formatted = []
        recent = self.state.messages[-(self.state.max_history * 2):]
        for msg in recent:
            formatted.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(formatted)

    def _extract_tool_calls(self, result: Dict) -> List[Dict]:
        """提取工具调用"""
        tool_calls = []
        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for call in msg.tool_calls:
                    tool_calls.append({
                        "tool": call.get("name"),
                        "args": call.get("args"),
                    })
        self.state.tool_history.extend(tool_calls)
        return tool_calls

    def _generate_session_id(self) -> str:
        """生成会话ID"""
        import hashlib
        content = "".join([m["content"] for m in self.state.messages[:2]])
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def _get_state_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        return {
            "session_id": self.state.session_id,
            "messages": self.state.messages,
            "tool_history": self.state.tool_history,
            "reflection_history": self.state.reflection_history,
            "error_count": self.state.error_count,
        }

    def reset(self):
        """重置状态"""
        self.state = CompleteAgentState(
            max_history=self.state.max_history,
            max_iterations=self.state.max_iterations,
            max_retries=self.state.max_retries,
        )

    def restore(self, session_id: str) -> bool:
        """
        恢复历史会话

        Args:
            session_id: 会话ID

        Returns:
            是否恢复成功
        """
        saved_state = self.state_manager.get_latest_state(session_id)
        if saved_state:
            self.state.messages = saved_state.get("messages", [])
            self.state.tool_history = saved_state.get("tool_history", [])
            self.state.session_id = session_id
            return True
        return False
```

### 7.2 创建完整演示脚本

```python
【文件: demo_complete_agent.py】（需新建）

"""
完整高级Agent演示
运行方式: python demo_complete_agent.py
"""

from src.complete_agent import CompleteAdvancedAgent


def main():
    print("=" * 70)
    print("完整高级Agent演示")
    print("=" * 70)

    # 创建Agent
    agent = CompleteAdvancedAgent(
        max_history=10,
        max_iterations=6,
        max_retries=3,
        enable_reflection=True,
    )

    # 演示多轮对话
    questions = [
        "帮我计算 (1+2)**3",
        "刚才的结果是多少？（测试记忆）",
        "统计'你好世界'的字符数",
        "从知识库查询环境保护知识",
    ]

    for i, question in enumerate(questions):
        print(f"\n【第{i+1}轮】问题：{question}")
        print("-" * 50)

        result = agent.chat(question)

        print(f"回答：{result['answer']}")
        print(f"工具调用：{result.get('tool_calls', [])}")
        print(f"反思评分：{result.get('reflection', 'N/A')[:100]}...")
        print(f"成功：{result['success']}")

    # 演示流式输出
    print("\n" + "=" * 70)
    print("流式输出演示")
    print("=" * 70)

    agent.reset()
    question = "计算 25*4，然后统计结果字符数"

    print(f"\n问题：{question}")
    print("-" * 50)

    for event in agent.chat_stream(question):
        if event["type"] == "thinking":
            print(f"[思考] {event['content'][:30]}...")
        elif event["type"] == "tool_call":
            print(f"[工具] 调用 {event['tool']}")
        elif event["type"] == "answer":
            print(f"[回答] {event['content']}")
        elif event["type"] == "complete":
            print(f"[完成] {event['message']}")


if __name__ == "__main__":
    main()
```

---

## 8. 阶段七：工具验证与安全增强

### 8.1 工具输入验证

```python
【文件: tools/validation.py】（需新建）

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
    def validate_expression(expr: str) -> bool:
        """验证数学表达式安全性"""
        # 检查长度
        if len(expr) > 100:
            return False
        # 检查非法字符
        allowed_chars = set("0123456789+-*/() .")
        if not all(c in allowed_chars for c in expr):
            return False
        return True

    @staticmethod
    def validate_text_length(text: str, max_length: int = 10000) -> bool:
        """验证文本长度"""
        return len(text) <= max_length

    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


# 使用验证器增强工具
from tools.basic_tools import safe_calculator, text_stats

def safe_calculator_with_validation(expression: str) -> Dict[str, Any]:
    """带验证的安全计算器"""
    # 先验证输入
    if not ToolInputValidator.validate_expression(expression):
        return {
            "ok": False,
            "data": None,
            "error": "表达式不安全或过长，请使用简单的数学运算",
        }
    # 再调用原工具
    return safe_calculator.invoke({"expression": expression})


def text_stats_with_validation(text: str, max_length: int = 10000) -> Dict[str, Any]:
    """带验证的文本统计"""
    if not ToolInputValidator.validate_text_length(text, max_length):
        return {
            "ok": False,
            "data": None,
            "error": f"文本过长（{len(text)} > {max_length}）",
        }
    return text_stats.invoke({"text": text})
```

### 8.2 API工具安全增强

```python
【文件: tools/api_tools.py】
【说明: 文件已存在但为空，需添加以下代码实现】

"""
API工具实现（带安全控制）
"""

from langchain_core.tools import tool
from typing import Dict, Any
import requests
import time


class APISafetyConfig:
    """API安全配置"""
    ALLOWED_DOMAINS = [
        "api.openweathermap.org",
        "api.example.com",
    ]
    MAX_TIMEOUT = 30
    MAX_RETRIES = 3


@tool
def safe_api_request(url: str, method: str = "GET", params: Dict = None) -> Dict[str, Any]:
    """
    安全API请求工具

    使用场景：
    - 需要调用外部API获取数据
    - 天气查询、数据获取等

    Args:
        url: API URL（必须是白名单域名）
        method: HTTP方法（GET/POST）
        params: 请求参数

    Returns:
        dict: API响应结果
    """
    # 1. 域名白名单检查
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc

    if domain not in APISafetyConfig.ALLOWED_DOMAINS:
        return {
            "ok": False,
            "data": None,
            "error": f"域名 {domain} 不在白名单中，不允许访问",
        }

    # 2. 方法限制
    if method not in ["GET", "POST"]:
        return {
            "ok": False,
            "data": None,
            "error": f"不支持的方法：{method}",
        }

    # 3. 执行请求
    retries = 0
    while retries < APISafetyConfig.MAX_RETRIES:
        try:
            start_time = time.time()
            response = requests.request(
                method,
                url,
                params=params,
                timeout=APISafetyConfig.MAX_TIMEOUT,
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                return {
                    "ok": True,
                    "data": response.json(),
                    "elapsed": elapsed,
                    "error": None,
                }
            else:
                return {
                    "ok": False,
                    "data": None,
                    "error": f"HTTP {response.status_code}",
                }

        except requests.Timeout:
            retries += 1
        except Exception as e:
            return {
                "ok": False,
                "data": None,
                "error": str(e),
            }

    return {
        "ok": False,
        "data": None,
        "error": f"请求超时（{retries}次重试后）",
    }
```

---

## 9. 练习清单

按顺序完成以下练习，逐步升级Agent：

| # | 练习内容 | 文件位置 | 实际状态 | 说明 |
|---|----------|----------|----------|------|
| 1 | 创建记忆管理器 | `src/advanced_agent.py` | ⚠️ 文件存在，需实现 | MemoryManager类 |
| 2 | 创建带记忆的Agent | `src/advanced_agent.py` | ⚠️ 文件存在，需实现 | AdvancedAgent类 |
| 3 | 创建记忆演示脚本 | `demo_advanced_agent.py` | ❌ 不存在，需新建 | 测试多轮对话 |
| 4 | 实现递归限制 | `src/advanced_agent.py` | ⚠️ 文件存在，需实现 | recursion_limit |
| 5 | 实现错误重试 | `src/advanced_agent.py` | ⚠️ 文件存在，需实现 | chat_with_retry |
| 6 | 创建错误处理器 | `tools/error_handling.py` | ❌ 不存在，需新建 | ToolErrorHandler |
| 7 | 实现自我反思 | `src/reflection.py` | ❌ 不存在，需新建 | 反思提示词 |
| 8 | 集成反思到Agent | `src/advanced_agent.py` | ⚠️ 文件存在，需实现 | chat_with_reflection |
| 9 | 创建工具链编排器 | `tools/tool_chain.py` | ❌ 不存在，需新建 | ToolChain类 |
| 10 | 实现流式输出 | `src/advanced_agent.py` | ⚠️ 文件存在，需实现 | chat_stream |
| 11 | 创建状态管理器 | `src/state_manager.py` | ❌ 不存在，需新建 | StateManager类 |
| 12 | 创建完整Agent | `src/complete_agent.py` | ❌ 不存在，需新建 | CompleteAdvancedAgent |
| 13 | 创建完整演示 | `demo_complete_agent.py` | ❌ 不存在，需新建 | 全功能演示 |
| 14 | 创建输入验证器 | `tools/validation.py` | ❌ 不存在，需新建 | ToolInputValidator |
| 15 | 创建安全API工具 | `tools/api_tools.py` | ⚠️ 文件存在，需实现 | safe_api_request |
| 16 | 更新工具导出 | `tools/__init__.py` | ✅ 已实现 | 需添加新工具导出 |
| 17 | 编写测试 | `tests/test_advanced_agent.py` | ❌ 不存在，需新建 | 单元测试 |

---

## 10. 附录：配置文件

### 10.1 更新 `tools/__init__.py`

```python
【文件: tools/__init__.py】（已存在，需添加新工具导出）

"""
工具模块导出入口
"""

# 基础工具
from .basic_tools import safe_calculator, get_current_time, text_stats, unit_convert

# 高级工具
from .advanced_tools import send_email_tool

# RAG工具
from .rag_tools import rag_qa, rag_rebuild, system_health

# API工具（可选）
try:
    from .api_tools import safe_api_request
except ImportError:
    safe_api_request = None

# 所有工具列表
ALL_TOOLS = [
    safe_calculator,
    get_current_time,
    text_stats,
    unit_convert,
    send_email_tool,
    rag_qa,
    rag_rebuild,
    system_health,
]

if safe_api_request:
    ALL_TOOLS.append(safe_api_request)
```

### 10.2 更新 `src/config.py`

```python
【文件: src / config.py】（已存在，需添加Agent配置）

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ============ API配置 ============
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv(
        "OPENAI_API_BASE",
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # ============ 模型配置 ============
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen-turbo")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")

    # ============ Agent配置 ============
    AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "6"))
    AGENT_MAX_RETRIES = int(os.getenv("AGENT_MAX_RETRIES", "3"))
    AGENT_MAX_HISTORY = int(os.getenv("AGENT_MAX_HISTORY", "10"))
    AGENT_ENABLE_REFLECTION = os.getenv("AGENT_ENABLE_REFLECTION", "true").lower() == "true"
    AGENT_STATE_DIR = os.getenv("AGENT_STATE_DIR", "../../agent_states")

    # ============ 工具配置 ============
    TOOL_TIMEOUT = float(os.getenv("TOOL_TIMEOUT", "30.0"))
    TOOL_MAX_RETRIES = int(os.getenv("TOOL_MAX_RETRIES", "3"))

    # ============ 文档处理配置 ============
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    SEPARETORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]

    # ============ 路径配置 ============
    VECTOR_DB_PATH = "../../chroma_db"
    KNOWLEDGE_PATH = "../../data/knowledge"

    # ============ 检索配置 ============
    RETRIEVE_TOP_K = 3
```

### 10.3 测试文件示例

```python
【文件: tests/test_advanced_agent.py】（需新建）

"""
高级Agent测试
"""

import pytest
from src.advanced_agent import AdvancedAgent, MemoryManager


class TestMemoryManager:
    """记忆管理器测试"""

    def test_add_message(self):
        """测试添加消息"""
        memory = MemoryManager(max_history=5)
        memory.add_message("user", "你好")
        memory.add_message("assistant", "你好！")

        history = memory.get_history()
        assert len(history) == 2

    def test_max_history_limit(self):
        """测试历史限制"""
        memory = MemoryManager(max_history=2)

        # 添加6条消息（3轮对话）
        for i in range(3):
            memory.add_message("user", f"问题{i}")
            memory.add_message("assistant", f"回答{i}")

        history = memory.get_history()
        # 应只保留最近2轮（4条）
        assert len(history) <= 4

    def test_clear(self):
        """测试清空"""
        memory = MemoryManager(max_history=5)
        memory.add_message("user", "测试")
        memory.clear()
        assert len(memory.get_history()) == 0


class TestAdvancedAgent:
    """高级Agent测试"""

    def test_chat_basic(self):
        """基础对话测试"""
        agent = AdvancedAgent(max_history=5, max_iterations=6)
        result = agent.chat("现在几点")

        assert "answer" in result
        assert result["answer"] is not None

    def test_memory_preservation(self):
        """记忆保持测试"""
        agent = AdvancedAgent(max_history=5, max_iterations=6)

        # 第一轮
        agent.chat("帮我计算 1+2")

        # 第二轮测试记忆
        result = agent.chat("刚才的结果是多少")
        history = result["history"]

        # 历史中应有第一轮对话
        assert len(history) >= 4

    def test_reset(self):
        """重置测试"""
        agent = AdvancedAgent(max_history=5, max_iterations=6)
        agent.chat("测试")
        agent.reset()

        history = agent.memory.get_history()
        assert len(history) == 0
```

---

## 总结

通过本指南，你将能够：

1. **增强记忆系统** - Agent能记住上下文
2. **添加递归限制** - 防止无限循环
3. **实现错误处理** - 自动重试与恢复
4. **添加自我反思** - 评估并修正回答
5. **编排工具链** - 多工具协同执行
6. **支持流式输出** - 实时返回结果
7. **持久化状态** - 会话恢复与调试

所有代码位置均已标明，按练习清单逐步完成即可升级为高级Agent。