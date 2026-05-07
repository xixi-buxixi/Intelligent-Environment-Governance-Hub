# Tools开发指南（优化版）— LangChain 1.0+ 补丁：替换 AgentExecutor

你遇到的报错现象一般是：

```python
from langchain.agents import AgentExecutor
# ImportError: cannot import name 'AgentExecutor' from 'langchain.agents'
```

原因：**LangChain 1.0+ 精简了旧的 Agents API，`AgentExecutor` 在新版中被移除/迁移**。  
官方推荐的新写法是使用 `create_agent`（底层基于 LangGraph 运行时）。

> 你原文档《Tools开发指南_优化版.md》里 **第 7 章 “Agent 集成”** 用的是旧写法（`AgentExecutor + create_tool_calling_agent`）。  
> 下面内容可以直接复制，替换原文 **7.1 / 7.2**。

---

## 7. 阶段 4：Agent 集成（LangChain 1.0+ 新写法）

### 7.1 创建 Agent 实现文件（新版本）

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
    """
    创建环境小助手 Agent（LangChain 1.0+）

    核心变化：
    - 不再使用 AgentExecutor
    - 直接用 create_agent 得到一个“可运行的 Agent”（它本身就是 runnable）
    """

    # 1) 模型（大脑）
    llm = ChatTongyi(
        model_name="qwen-plus",
        dashscope_api_key=Config.OPENAI_API_KEY,
    )

    # 2) 工具（手）
    tools = [safe_calculator, get_current_time, text_stats, unit_convert]

    # 3) 系统提示词（规则）
    system_prompt = (
        "你是环境小助手。遇到计算/统计/时间/单位转换问题必须调用对应工具。"
        "工具结果为准，不要编造。不确定的信息要说不知道。"
    )

    # 4) 创建 Agent（新API）
    agent = create_agent(
        model=llm,              # 也可以传模型字符串，如 'openai:gpt-5'
        tools=tools,
        system_prompt=system_prompt,
        # 可选：name="environment_agent"
    )

    return agent


def run_agent(question: str) -> dict:
    """
    运行 Agent（新版本）

    说明：
    - create_agent 的 invoke 输入通常是 {"messages": [...]} 的形式
    - 返回值是一个 state dict，其中包含 messages（含工具调用过程）
    """
    agent = create_environment_agent()
    return agent.invoke({"messages": [HumanMessage(content=question)]})
```

#### 运行结果怎么取“最终回答”？

```python
result = run_agent("帮我算 (1+2)**3，统计'你好 world'的英文单词数，告诉我现在时间。")
final_answer = result["messages"][-1].content
print(final_answer)
```

#### 怎么看“中间工具调用过程”？

`result["messages"]` 里会包含：
- HumanMessage（用户问题）
- AIMessage（模型的工具调用请求）
- ToolMessage（工具执行结果）
- AIMessage（模型最终回答）

你打印 `result["messages"]` 就能看到完整过程回放。

---

### 7.2 创建 Agent 演示脚本（新版本）

```python
【文件: demo_agent.py】

"""
Agent演示脚本（LangChain 1.0+）
运行方式: python demo_agent.py
"""

from src.agent import run_agent


def main():
    question = "帮我算 (1+2)**3，统计'你好 world'的英文单词数，最后告诉我现在时间。"
    result = run_agent(question)

    print("=" * 50)
    print("最终回答:")
    print(result["messages"][-1].content)
    print("=" * 50)

    print("过程回放（messages）:")
    for msg in result["messages"]:
        # 只做简单展示：打印消息类型 + 内容
        print(f"[{msg.__class__.__name__}] {getattr(msg, 'content', '')}")


if __name__ == "__main__":
    main()
```

---

## 兼容方案（如果你不想改代码）

如果你想继续使用旧写法（`AgentExecutor`），通常有两条路：

1) **降级到 0.3.x**（你原项目依赖就是这一代）  
2) **使用兼容包 `langchain-classic`**（把旧 API 留在 classic 里）  

但既然你明确要“使用最新的方法”，建议采用上面的 `create_agent` 方案。

---

## 你应该怎么改你原文档？

在你上传的《Tools开发指南_优化版.md》中：

- 把 **7.1** 里 `AgentExecutor, create_tool_calling_agent` 那段代码，替换为本补丁的 **7.1 新版本代码**
- 把 **7.2** 演示脚本替换为本补丁的 **7.2 新版本脚本**
- 运行时用：`python demo_agent.py`

