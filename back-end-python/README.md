# LangChain RAG + Agent 环境小助手

## 项目简介
本项目是一个基于 LangChain 的环境小助手，支持 RAG 知识问答与 Agent 工具调用两种模式，并可通过接口参数切换。

## 目录结构
- `src/` 核心业务代码
- `tools/` 工具定义与集成
- `tests/` 测试代码
- `examples/` 演示脚本
- `docs/learning/` 学习文档与改造清单
- `runtime/` 运行时产物（日志、状态、向量库）

## 环境准备
1. 安装依赖（任选其一）
- `pip install -r requirement.txt`
- 或使用 `pyproject.toml` 对应的工具安装
2. 复制环境变量模板
- 将 `.env.example` 复制为 `.env` 并填写 `OPENAI_API_KEY`

## 启动命令
- 构建知识库：`python main.py build`
- 命令行问答（RAG）：`python main.py ask "什么是垃圾分类" rag`
- 命令行问答（Agent）：`python main.py ask "帮我计算(1+2)**3" agent`
- 命令行问答（Hybrid）：`python main.py ask "请结合知识库回答" hybrid`
- 启动 API：`python app.py`

## API 示例
`POST /api/chat`

请求体：
```json
{
  "question": "什么是垃圾分类？",
  "mode": "rag"
}
```

`mode` 支持：`rag`、`agent`、`hybrid`

## 测试
- 运行全部测试：`python -m pytest -v`
- 运行工具测试：`python -m pytest tests/test_tools.py -v`
