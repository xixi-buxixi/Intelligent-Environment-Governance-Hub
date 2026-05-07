# 项目整理与融合详细任务清单（含代码修改示例）

## 0. 执行总原则
1. 先做结构清理，再做功能融合，最后做测试和文档。
2. 每一步改动后都执行一次最小验证，避免“最后一次性爆雷”。
3. 只保留一条主线：`环境小助手 = RAG + Agent 可切换`。

---

## 1. 目录重构（先清场）

### 1.1 新建标准目录
1. 新建 `docs/learning/`、`examples/`、`runtime/`。
2. `runtime/` 下预留：`logs/`、`agent_states/`、`chroma_db/`。

### 1.2 移动散乱文件
1. `demo_*.py` 移到 `examples/`。
2. 学习型文档（开发指南、补丁、流程梳理）移到 `docs/learning/`。

### 1.3 验收
1. 根目录只保留：入口文件、配置、源码目录、测试目录、README。
2. 不再出现“演示脚本 + 文档 + runtime 文件”混在根目录。

---

## 2. 配置治理（先修高风险项）

### 2.1 删除硬编码密钥，统一路径配置
文件路径：`D:/My/python/project/Langchain-demo/project/src/config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # API配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 不允许硬编码默认值
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    # 模型配置
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "tongyi")  # tongyi / openai_compat
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")

    # Agent配置
    AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "6"))
    AGENT_MAX_RETRIES = int(os.getenv("AGENT_MAX_RETRIES", "3"))
    AGENT_MAX_HISTORY = int(os.getenv("AGENT_MAX_HISTORY", "10"))
    AGENT_ENABLE_REFLECTION = os.getenv("AGENT_ENABLE_REFLECTION", "true").lower() == "true"
    AGENT_STATE_DIR = os.getenv("AGENT_STATE_DIR", "./runtime/agent_states")

    # 路径配置
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./runtime/chroma_db")
    KNOWLEDGE_PATH = os.getenv("KNOWLEDGE_PATH", "./data/knowledge")
    LOG_DIR = os.getenv("LOG_DIR", "./runtime/logs")

    # 检索配置
    RETRIEVE_TOP_K = int(os.getenv("RETRIEVE_TOP_K", "3"))
```

### 2.2 增加环境变量模板
文件路径：`D:/My/python/project/Langchain-demo/project/.env.example`

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

LLM_PROVIDER=tongyi
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v3

VECTOR_DB_PATH=./runtime/chroma_db
KNOWLEDGE_PATH=./data/knowledge
LOG_DIR=./runtime/logs
AGENT_STATE_DIR=./runtime/agent_states

RETRIEVE_TOP_K=3
AGENT_MAX_ITERATIONS=6
AGENT_MAX_RETRIES=3
AGENT_MAX_HISTORY=10
AGENT_ENABLE_REFLECTION=true
```

### 2.3 验收
1. 仓库中不再出现真实密钥。
2. 改 `.env` 即可切换路径和模型。

---

## 3. 统一模型工厂（解决 Tongyi/OpenAI 混用）

### 3.1 新建模型工厂
文件路径：`D:/My/python/project/Langchain-demo/project/src/llm/factory.py`

```python
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI
from src.config import Config


def get_chat_model(temperature: float = 0.7):
    provider = Config.LLM_PROVIDER.lower()

    if provider == "tongyi":
        return ChatTongyi(
            model_name=Config.LLM_MODEL,
            temperature=temperature,
            dashscope_api_key=Config.OPENAI_API_KEY,
        )

    if provider == "openai_compat":
        return ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=temperature,
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_API_BASE,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {Config.LLM_PROVIDER}")
```

### 3.2 替换 RAG 中直接实例化
文件路径：`D:/My/python/project/Langchain-demo/project/src/rag_chain.py`

```python
# 删除：
# from langchain_community.chat_models.tongyi import ChatTongyi

from src.llm.factory import get_chat_model

# 在 __init__ 中替换：
self.llm = get_chat_model(temperature=temperature)
```

### 3.3 替换 Agent/Parser 中直接实例化
1. `src/agent.py`、`src/advanced_agent.py`、`src/complete_agent.py`、`src/agents/structured_output_agent.py`、`src/parsers/robust_parser.py`
2. 原则：全部改为 `from src.llm.factory import get_chat_model`，并通过工厂获取模型。

### 3.4 验收
1. 项目中不再手写 `ChatTongyi(...)` 或 `ChatOpenAI(...)`（允许工厂中出现）。
2. 只改 `.env` 的 `LLM_PROVIDER` 就能切换实现。

---

## 4. 统一导入路径（修复 `from project...`）

### 4.1 必改文件示例

文件路径：`D:/My/python/project/Langchain-demo/project/src/advanced_agent.py`

```python
# 修改前
from project.src.parsers.robust_parser import RobustJSONParser
from project.src.reflection import REFLECTION_PROMPT, get_reflection_format_instructions, ReflectionResult

# 修改后
from src.parsers.robust_parser import RobustJSONParser
from src.reflection import REFLECTION_PROMPT, get_reflection_format_instructions, ReflectionResult
```

文件路径：`D:/My/python/project/Langchain-demo/project/src/llm/function_calling.py`

```python
# 修改前
from project.src.config import Config

# 修改后
from src.config import Config
```

文件路径：`D:/My/python/project/Langchain-demo/project/tests/tool_chain_test.py`

```python
# 修改前
from project.tools.tool_chain import ToolChain, ToolStep

# 修改后
from tools.tool_chain import ToolChain, ToolStep
```

### 4.2 去掉动态注入 `sys.path`
文件路径：`D:/My/python/project/Langchain-demo/project/tools/tool_integration.py`

```python
# 删除这段路径注入逻辑：
# import sys
# from pathlib import Path
# project_root = Path(__file__).parent.parent
# if str(project_root) not in sys.path:
#     sys.path.insert(0, str(project_root))
```

### 4.3 验收
1. 全量搜索无 `from project.` 残留。
2. 从项目根目录运行脚本不需要手工改 `PYTHONPATH`。

---

## 5. 融合主线：让 CLI/API 同时支持 RAG 与 Agent

### 5.1 新建统一服务层
文件路径：`D:/My/python/project/Langchain-demo/project/src/services/assistant_service.py`

```python
from src.config import Config
from src.vectorstore import VectorStoreManager
from src.rag_chain import RAGChain
from src.complete_agent import CompleteAdvancedAgent


class AssistantService:
    def __init__(self):
        self._agent = CompleteAdvancedAgent(
            max_history=Config.AGENT_MAX_HISTORY,
            max_iterations=Config.AGENT_MAX_ITERATIONS,
            max_retries=Config.AGENT_MAX_RETRIES,
            enable_reflection=Config.AGENT_ENABLE_REFLECTION,
            state_dir=Config.AGENT_STATE_DIR,
        )
        self._rag_chain = None

    def _get_rag_chain(self):
        if self._rag_chain is None:
            manager = VectorStoreManager(
                persist_directory=Config.VECTOR_DB_PATH,
                api_key=Config.OPENAI_API_KEY,
                embedding_model=Config.EMBEDDING_MODEL,
            )
            retriever = manager.get_retriever(top_k=Config.RETRIEVE_TOP_K)
            self._rag_chain = RAGChain(
                retriever=retriever,
                model_name=Config.LLM_MODEL,
                api_key=Config.OPENAI_API_KEY,
            )
        return self._rag_chain

    def ask(self, question: str, mode: str = "rag") -> dict:
        mode = mode.lower()
        if mode == "agent":
            result = self._agent.chat(question)
            return {"mode": "agent", "answer": result.get("answer", ""), "meta": result}
        if mode == "hybrid":
            agent_result = self._agent.chat(question)
            if agent_result.get("answer"):
                return {"mode": "hybrid-agent", "answer": agent_result["answer"], "meta": agent_result}
            rag_answer = self._get_rag_chain().invoke(question)
            return {"mode": "hybrid-rag", "answer": rag_answer, "meta": {}}

        rag = self._get_rag_chain()
        return {"mode": "rag", "answer": rag.invoke(question), "meta": {}}
```

### 5.2 CLI 接入服务层
文件路径：`D:/My/python/project/Langchain-demo/project/main.py`

```python
# 增加导入
from src.services.assistant_service import AssistantService

# 在 ask_question 中改为：
def ask_question(question: str, mode: str = "rag"):
    service = AssistantService()
    result = service.ask(question, mode=mode)
    print(result["answer"])

# 命令行新增
# python main.py ask "xxx" agent
# python main.py ask "xxx" hybrid
```

### 5.3 API 接入服务层
文件路径：`D:/My/python/project/Langchain-demo/project/app.py`

```python
# 新增
from src.services.assistant_service import AssistantService
assistant_service = AssistantService()

# /api/chat 中读取 mode
mode = data.get("mode", "rag")
result = assistant_service.ask(question, mode=mode)
return jsonify({
    "question": question,
    "mode": result["mode"],
    "answer": result["answer"],
    "meta": result.get("meta", {})
})
```

### 5.4 验收
1. 同一接口可通过 `mode` 切换回答策略。
2. CLI 与 API 都走同一服务层，逻辑不再分叉复制。

---

## 6. 运行产物隔离与忽略规则

### 6.1 新建忽略文件
文件路径：`D:/My/python/project/Langchain-demo/project/.gitignore`

```gitignore
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/

.env
runtime/
```

### 6.2 更新日志目录初始化
文件路径：`D:/My/python/project/Langchain-demo/project/app.py`

```python
from src.config import Config
os.makedirs(Config.LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(Config.LOG_DIR, 'app.log')
)
```

### 6.3 验收
1. 新日志、状态、向量库都在 `runtime/` 下。
2. `git status` 不再显示运行产物。

---

## 7. 测试修复与重组

### 7.1 修复 `test_tools.py` 与真实返回结构不一致问题
文件路径：`D:/My/python/project/Langchain-demo/project/tests/test_tools.py`

```python
def test_basic_stats(self):
    result = text_stats.invoke({"text": "Hello world! This is a test."})
    assert result["ok"] is True
    assert result["data"]["chinese_chars"] == 0
    assert result["data"]["english_words"] == 6
    assert result["data"]["total_chars"] == 28
    assert result["data"]["sentences_estimate"] == 2
```

### 7.2 区分单测与集成测试
1. `tests/unit/`：`test_tools.py`、`test_validators.py`
2. `tests/integration/`：`test_advanced_agent.py`、`test_structureOutputAgent.py`

文件路径：`D:/My/python/project/Langchain-demo/project/pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v"
pythonpath = ["."]
markers = [
    "integration: tests that require model API and external services"
]
```

### 7.3 对集成测试加标记
文件路径：`D:/My/python/project/Langchain-demo/project/tests/integration/test_advanced_agent.py`

```python
import pytest

@pytest.mark.integration
def test_chat_basic():
    ...
```

### 7.4 验收
1. 默认跑单测稳定通过。
2. `-m integration` 时才跑外部依赖测试。

---

## 8. 修复明显逻辑风险点（建议立刻改）

### 8.1 `main.py` 回答打印缩进错误
当前 `ask_question` 中回答在文档循环里重复打印。应把生成回答移出循环。

文件路径：`D:/My/python/project/Langchain-demo/project/main.py`

```python
docs = rag_chain.get_retrieved_docs(question)
for i, doc in enumerate(docs, 1):
    source = doc.metadata.get("source", "未知")
    print(f"\n文档{i} [来源: {source}]:")
    print(doc.page_content[:150] + "...")

print("\n" + "=" * 60)
print("【AI回答】")
print("-" * 40)
answer = rag_chain.invoke(question)
print(answer)
print("=" * 60)
```

### 8.2 `complete_agent.py` 反思递归风险
`_reflect_and_revise` 中 `revision = self.chat(...)` 可能引发深层递归。建议增加一次性修订函数而不是再次调用 `chat` 全流程。

文件路径：`D:/My/python/project/Langchain-demo/project/src/complete_agent.py`

```python
def _revise_once(self, question: str, original_answer: str, reflection_text: str) -> str:
    prompt = f"""
问题：{question}
原始回答：{original_answer}
评估意见：{reflection_text}
请直接给出修正后的最终回答，不要输出评分过程。
"""
    response = self.llm.invoke([{"role": "user", "content": prompt}])
    return response.content

# 在 _reflect_and_revise 中替换
if needs_revision:
    result["answer"] = self._revise_once(question, result["answer"], reflection_text)
    result["revised"] = True
```

### 8.3 验收
1. 同一问题不会触发嵌套 `chat -> reflect -> chat` 链。
2. 反思修订最多执行一次。

---

## 9. README 收口（必须和代码一致）

### 9.1 README 必含章节
1. 项目目标（1段话）
2. 目录结构（重构后）
3. 环境变量与 `.env.example`
4. 启动方式（CLI/API + mode 参数）
5. 测试命令（unit / integration）
6. 常见问题

### 9.2 推荐命令示例
文件路径：`D:/My/python/project/Langchain-demo/project/README.md`

```bash
# 构建知识库
python main.py build

# RAG模式问答
python main.py ask "什么是垃圾分类" rag

# Agent模式问答
python main.py ask "帮我计算(1+2)**3" agent

# 启动API
python app.py
```

### 9.3 验收
1. 新成员只看 README 能跑通。
2. README 命令与真实代码参数完全一致。

---

## 10. 分阶段执行计划（可直接照做）

1. 第1天  
目录重构 + `.gitignore` + `config.py` 安全改造 + `.env.example`

2. 第2天  
`llm/factory.py` 落地 + 全量替换模型实例化 + 修复导入路径

3. 第3天  
`assistant_service.py` 落地 + `main.py/app.py` 接入 `mode`

4. 第4天  
测试修复与分层 + 修正关键逻辑风险（`main.py`、`complete_agent.py`）

5. 第5天  
README 重写 + 回归验证 + 清理遗留文件

---

## 11. 最终验收清单（上线前）
1. `python main.py build` 正常。
2. `python main.py ask "测试" rag|agent|hybrid` 三种模式正常。
3. `python app.py` 后 `/api/chat` 支持 `mode` 参数。
4. 默认单测通过。
5. 仓库无敏感信息、无运行垃圾文件、无错误导入路径。
