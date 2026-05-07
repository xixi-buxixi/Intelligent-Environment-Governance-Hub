# RAG环境小助手开发指南

> 本指南将带你从零开始构建一个基于LangChain的RAG（检索增强生成）环境小助手，最终通过Flask封装为API服务。

---

## 目录

1. [项目概述](#1-项目概述)
2. [环境准备](#2-环境准备)
3. [LangChain核心概念](#3-langchain核心概念)
4. [第一阶段：基础RAG实现](#4-第一阶段基础rag实现)
5. [第二阶段：优化与增强](#5-第二阶段优化与增强)
6. [第三阶段：Flask API封装](#6-第三阶段flask-api封装)
7. [第四阶段：进阶功能](#7-第四阶段进阶功能)
8. [常见问题与解决方案](#8-常见问题与解决方案)

---

## 1. 项目概述

### 1.1 什么是RAG？

RAG（Retrieval-Augmented Generation）是一种结合检索和生成的技术：
- **检索（Retrieval）**：从知识库中查找相关文档
- **增强（Augmented）**：将检索结果作为上下文
- **生成（Generation）**：基于上下文生成准确回答

### 1.2 项目目标

构建一个环境小助手，能够：
- 回答环境保护相关问题
- 基于本地知识库提供准确信息
- 通过API接口提供服务

### 1.3 技术栈

| 组件 | 技术选择 | 说明 |
|------|---------|------|
| LLM | Qwen（通义千问） | 使用 ChatTongyi 官方集成 |
| Embeddings | Qwen Embeddings | 使用 DashScopeEmbeddings 官方集成 |
| Vector Store | Chroma | 向量数据库 |
| Web Framework | Flask | API服务 |
| LangChain | langchain, langchain-community | 核心框架 |

### 1.4 最终项目结构预览

```
project/
├── .env                          # 环境变量配置
├── requirements.txt              # 依赖列表
├── main.py                       # 命令行入口
├── app.py                        # Flask API服务
│
├── data/
│   └── knowledge/               # 知识库文档
│       ├── 垃圾分类指南.txt
│       ├── 环境保护基础知识.txt
│       └── 节能减排小知识.txt
│
├── chroma_db/                   # 向量数据库（自动生成）
│
└── src/
    ├── __init__.py
    ├── config.py                # 配置管理
    ├── document_processor.py    # 文档处理
    ├── vectorstore.py           # 向量存储
    └── rag_chain.py             # RAG链
```

---

## 2. 环境准备

### 2.1 本阶段目标

创建项目基础结构，安装依赖，配置环境变量。

### 2.2 本阶段文件目录

```
project/                          <- 项目根目录
├── .env                          <- 创建：环境变量配置
├── requirements.txt              <- 创建：依赖列表
├── data/
│   └── knowledge/               <- 创建：知识库文档目录
│       ├── 垃圾分类指南.txt      <- 创建：知识文档
│       ├── 环境保护基础知识.txt  <- 创建：知识文档
│       └── 节能减排小知识.txt    <- 创建：知识文档
└── src/
    └── __init__.py              <- 创建：包初始化文件
```

### 2.3 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2.4 安装依赖

```bash
# 核心依赖
pip install langchain langchain-community langchain-core langchain-chroma langchain-text-splitters

# 向量数据库
pip install chromadb

# 文档加载
pip install pypdf

# Web框架
pip install flask flask-cors

# 环境变量管理
pip install python-dotenv
```

### 2.5 创建 requirements.txt

在项目根目录创建 `requirements.txt`：

```
langchain>=1.0.0
langchain-community>=0.4.0
langchain-core>=1.0.0
langchain-chroma>=1.1.0
langchain-text-splitters>=1.1.0
chromadb>=0.4.22
pypdf>=4.0.0
flask>=3.0.0
flask-cors>=4.0.0
python-dotenv>=1.0.0
```

### 2.6 创建知识库目录

```bash
# 创建目录结构
mkdir -p data/knowledge
mkdir -p src
```

### 2.7 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# 通义千问API配置
# 获取API Key: https://dashscope.console.aliyun.com/apiKey
OPENAI_API_KEY=sk-your-dashscope-api-key-here

# 模型配置
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v3
```

### 2.8 创建 src/__init__.py

在 `src/` 目录下创建 `__init__.py`：

```python
# src包初始化文件
```

### 2.9 创建知识库文档

在 `data/knowledge/` 目录下创建示例文档：

**垃圾分类指南.txt**：
```
# 垃圾分类指南

## 什么是垃圾分类？

垃圾分类是指按照垃圾的不同成分、属性、利用价值以及对环境的影响，并根据不同处置方式的要求，分成属性不同的若干种类。

## 垃圾分类的种类

### 一、可回收物（蓝色垃圾桶）

可回收物是指适宜回收利用和资源化利用的生活废弃物。

1. **纸类**：报纸、纸箱、书本等
2. **塑料**：塑料瓶、塑料桶、塑料玩具等
3. **金属**：易拉罐、金属罐头盒等
4. **玻璃**：玻璃瓶、玻璃杯等
5. **织物**：旧衣服、床单被罩等

### 二、有害垃圾（红色垃圾桶）

有害垃圾是指对人体健康或者自然环境造成直接或者潜在危害的生活废弃物。

1. **废电池**：充电电池、纽扣电池等
2. **废灯管**：灯管、节能灯等
3. **废药品**：过期药品、药品包装等
4. **废油漆**：油漆桶、染发剂等

### 三、厨余垃圾（绿色垃圾桶）

厨余垃圾是指居民日常生活及食品加工、饮食服务等活动中产生的垃圾。

1. **食材废料**：菜叶、果皮、蛋壳等
2. **剩饭剩菜**：米饭、面条、肉类等
3. **过期食品**：过期面包、饼干等

### 四、其他垃圾（灰色垃圾桶）

其他垃圾是指除可回收物、有害垃圾、厨余垃圾以外的其他生活废弃物。

1. **卫生纸**：餐巾纸、卫生纸等
2. **一次性餐具**：一次性筷子、餐盒等
3. **烟蒂**：烟头、烟灰等
```

### 2.10 本阶段完成检查

- [ ] 虚拟环境已创建并激活
- [ ] 依赖已安装
- [ ] `.env` 文件已配置正确的 API Key
- [ ] `data/knowledge/` 目录已创建并包含知识文档
- [ ] `src/__init__.py` 文件已创建

---

## 3. LangChain核心概念

### 3.1 核心组件关系图

```
┌─────────────────────────────────────────────────────────┐
│                      RAG Pipeline                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐     │
│  │ Documents │───▶│  Splitter │───▶│  Embeddings   │     │
│  └──────────┘    └──────────┘    └──────────────┘     │
│                                         │              │
│                                         ▼              │
│                                  ┌──────────────┐     │
│                                  │  VectorStore │     │
│                                  └──────────────┘     │
│                                         │              │
│         ┌───────────────────────────────┘              │
│         │                                              │
│         ▼                                              │
│  ┌──────────────┐    ┌──────────┐    ┌──────────┐     │
│  │   Retriever   │───▶│  Prompt  │───▶│   LLM    │     │
│  └──────────────┘    └──────────┘    └──────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心概念解释

#### Document（文档）
```python
from langchain_core.documents import Document

# 文档是LangChain的基本数据单元
doc = Document(
    page_content="这是文档内容",
    metadata={"source": "环境报告.pdf", "page": 1}
)
```

#### Document Loader（文档加载器）
```python
from langchain_community.document_loaders import PyPDFLoader, TextLoader

# 加载PDF
loader = PyPDFLoader("环境报告.pdf")
docs = loader.load()

# 加载文本
loader = TextLoader("知识.txt", encoding="utf-8")
docs = loader.load()
```

#### Text Splitter（文本分割器）
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 将长文档分割成小块
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # 每块最大字符数
    chunk_overlap=50,    # 块之间的重叠
    length_function=len,
)
chunks = splitter.split_documents(docs)
```

#### Embeddings（嵌入模型）- 使用 DashScope
```python
from langchain_community.embeddings import DashScopeEmbeddings

# 使用阿里云通义千问嵌入模型（推荐，无需网络下载tiktoken）
embeddings = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key="your-api-key"
)
```

#### Vector Store（向量存储）
```python
from langchain_chroma import Chroma

# 创建向量数据库
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
```

#### Retriever（检索器）
```python
# 从向量存储创建检索器
retriever = vectorstore.as_retriever(
    search_type="similarity",  # 相似度搜索
    search_kwargs={"k": 3}     # 返回前3个最相似的文档
)
```

#### LLM（大语言模型）- 使用 ChatTongyi
```python
from langchain_community.chat_models.tongyi import ChatTongyi

# 使用阿里云通义千问（推荐，无SSL证书问题）
llm = ChatTongyi(
    model_name="qwen-plus",
    dashscope_api_key="your-api-key"
)
```

---

## 4. 第一阶段：基础RAG实现

### 4.1 本阶段目标

实现完整的RAG流程：文档加载 → 向量化 → 存储 → 检索 → 生成回答。

### 4.2 本阶段文件目录

**阶段开始时**：
```
project/
├── .env                          # 已存在
├── requirements.txt              # 已存在
├── data/
│   └── knowledge/               # 已存在
│       ├── 垃圾分类指南.txt
│       ├── 环境保护基础知识.txt
│       └── 节能减排小知识.txt
└── src/
    └── __init__.py              # 已存在
```

**阶段结束时**：
```
project/
├── .env                          # 已存在
├── requirements.txt              # 已存在
├── main.py                       # [新增] 命令行入口
├── data/
│   └── knowledge/               # 已存在
│       ├── 垃圾分类指南.txt
│       ├── 环境保护基础知识.txt
│       └── 节能减排小知识.txt
├── chroma_db/                   # [自动生成] 向量数据库
└── src/
    ├── __init__.py              # 已存在
    ├── config.py                # [新增] 配置管理
    ├── document_processor.py    # [新增] 文档处理
    ├── vectorstore.py           # [新增] 向量存储
    └── rag_chain.py             # [新增] RAG链
```

### 4.3 步骤1：创建配置文件

在 `src/` 目录下创建 `config.py`：

```python
"""
配置文件 - 集中管理所有配置项

文件位置: src/config.py
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ============ API配置 ============
    # 阿里云通义千问API Key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # ============ 模型配置 ============
    # 对话模型
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
    # 嵌入模型
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")

    # ============ 文档处理配置 ============
    CHUNK_SIZE = 500  # 每块最大字符数
    CHUNK_OVERLAP = 50  # 块之间的重叠字符数
    SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]

    # ============ 路径配置 ============
    VECTOR_DB_PATH = "../../chroma_db"
    KNOWLEDGE_PATH = "../../data/knowledge"

    # ============ 检索配置 ============
    RETRIEVE_TOP_K = 3  # 检索返回的文档数量
```

### 4.4 步骤2：创建文档处理器

在 `src/` 目录下创建 `document_processor.py`：

```python
"""
文档处理器 - 加载和分割文档

文件位置: src/document_processor.py

学习要点：
1. Document是LangChain的基本数据单元
2. DocumentLoader负责从各种来源加载文档
3. TextSplitter将长文档分割成适合检索的小块
4. chunk_overlap确保上下文连续性
"""
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
import os
from src.config import Config


class DocumentProcessor:
    """文档处理器：加载和分割文档"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 创建文本分割器
        # 中文优化分隔符：优先按段落、句子分割
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=Config.SEPARATORS
        )

    def load_pdf(self, file_path: str) -> List[Document]:
        """加载PDF文件"""
        loader = PyPDFLoader(file_path)
        return loader.load()

    def load_text(self, file_path: str) -> List[Document]:
        """加载文本文件"""
        loader = TextLoader(file_path, encoding="utf-8")
        return loader.load()

    def load_directory(self, dir_path: str) -> List[Document]:
        """加载目录下所有文档"""
        documents = []

        # 遍历目录
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if file.endswith('.pdf'):
                        documents.extend(self.load_pdf(file_path))
                        print(f"  [OK] 加载PDF: {file}")
                    elif file.endswith('.txt'):
                        documents.extend(self.load_text(file_path))
                        print(f"  [OK] 加载文本: {file}")
                except Exception as e:
                    print(f"  [FAIL] 加载失败 {file}: {e}")

        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """分割文档为小块"""
        return self.text_splitter.split_documents(documents)

    def process(self, source_path: str) -> List[Document]:
        """
        完整处理流程：加载 -> 分割

        Args:
            source_path: 文件或目录路径

        Returns:
            分割后的文档块列表
        """
        print(f"正在加载文档: {source_path}")

        # 加载文档
        if os.path.isdir(source_path):
            documents = self.load_directory(source_path)
        elif os.path.isfile(source_path):
            if source_path.endswith('.pdf'):
                documents = self.load_pdf(source_path)
            else:
                documents = self.load_text(source_path)
        else:
            raise ValueError(f"路径不存在: {source_path}")

        print(f"加载了 {len(documents)} 个文档片段")

        # 分割文档
        chunks = self.split_documents(documents)
        print(f"分割成 {len(chunks)} 个文本块")

        return chunks
```

### 4.5 步骤3：创建向量存储管理器

在 `src/` 目录下创建 `vectorstore.py`：

```python
"""
向量存储管理器 - 创建和管理向量数据库

文件位置: src/vectorstore.py

学习要点：
1. Embeddings将文本转换为向量表示
2. VectorStore存储向量并支持相似度搜索
3. Chroma是轻量级本地向量数据库，适合学习
4. Retriever是VectorStore的检索接口

注意：使用 DashScopeEmbeddings 而非 OpenAIEmbeddings
      DashScopeEmbeddings 是阿里云官方集成，无需 tiktoken，避免网络问题
"""
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import DashScopeEmbeddings
from typing import List, Optional
import os


class VectorStoreManager:
    """向量存储管理器：创建和管理向量数据库"""

    def __init__(
        self,
        persist_directory: str,
        api_key: str,
        embedding_model: str = "text-embedding-v3",
    ):
        """
        初始化向量存储管理器

        Args:
            persist_directory: 向量数据库持久化目录
            api_key: 阿里云DashScope API密钥
            embedding_model: 嵌入模型名称
        """
        self.persist_directory = persist_directory
        self.api_key = api_key
        self.embedding_model = embedding_model

        # 使用 DashScopeEmbeddings（阿里云官方集成，无需 tiktoken）
        self.embeddings = DashScopeEmbeddings(
            model=embedding_model,
            dashscope_api_key=api_key,
        )
        self.vectorstore: Optional[Chroma] = None

    def create_from_documents(self, documents: List[Document]) -> Chroma:
        """
        从文档创建向量存储

        Args:
            documents: 文档列表

        Returns:
            向量存储实例
        """
        print(f"正在创建向量数据库...")
        print(f"  - 嵌入模型: {self.embedding_model}")
        print(f"  - 文档数量: {len(documents)}")

        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
        )
        print(f"向量数据库创建完成，保存至: {self.persist_directory}")
        return self.vectorstore

    def load(self) -> Chroma:
        """
        加载已有向量存储

        Returns:
            向量存储实例
        """
        if not os.path.exists(self.persist_directory):
            raise ValueError(f"向量数据库不存在: {self.persist_directory}")

        print(f"正在加载向量数据库: {self.persist_directory}")

        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )
        return self.vectorstore

    def get_retriever(self, top_k: int = 3):
        """
        获取检索器

        Args:
            top_k: 返回的文档数量

        Returns:
            检索器实例
        """
        if self.vectorstore is None:
            self.load()

        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": top_k}
        )

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """
        相似度搜索

        Args:
            query: 查询文本
            k: 返回的文档数量

        Returns:
            相似文档列表
        """
        if self.vectorstore is None:
            self.load()

        return self.vectorstore.similarity_search(query, k=k)
```

### 4.6 步骤4：创建RAG链

在 `src/` 目录下创建 `rag_chain.py`：

```python
"""
RAG问答链 - 构建检索增强生成链

文件位置: src/rag_chain.py

学习要点：
1. PromptTemplate定义提示词模板
2. RunnablePassthrough传递原始问题
3. | 操作符连接组件形成处理链（LCEL语法）
4. StrOutputParser将LLM输出转为字符串
5. 这就是LangChain Expression Language (LCEL)的核心用法

注意：使用 ChatTongyi 而非 ChatOpenAI
      ChatTongyi 是阿里云官方集成，无SSL证书问题
"""
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import List


class RAGChain:
    """RAG问答链"""

    # 提示词模板
    PROMPT_TEMPLATE = """你是一个专业的环境小助手，请根据以下上下文信息回答用户问题。
如果上下文中没有相关信息，请诚实地说"我没有找到相关信息"，不要编造答案。

上下文信息：
{context}

用户问题：{question}

请给出详细、准确的回答："""

    def __init__(
        self,
        retriever,
        model_name: str = "qwen-plus",
        temperature: float = 0.7,
        api_key: str = None,
    ):
        """
        初始化RAG链

        Args:
            retriever: 检索器
            model_name: 模型名称
            temperature: 温度参数
            api_key: 阿里云DashScope API密钥
        """
        self.retriever = retriever

        # 使用 ChatTongyi（阿里云官方LangChain集成）
        print(f"初始化LLM：{model_name}")
        self.llm = ChatTongyi(
            model_name=model_name,
            temperature=temperature,
            dashscope_api_key=api_key,
        )

        # 创建提示词模板
        self.prompt = ChatPromptTemplate.from_template(self.PROMPT_TEMPLATE)

        # 构建RAG链
        self.chain = self._build_chain()

    def _build_chain(self):
        """
        构建RAG链

        LCEL链式调用流程：
        问题 -> 检索器获取文档 -> 格式化文档 -> 填充提示词 -> LLM生成 -> 输出
        """
        # 定义格式化文档的函数
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # 使用LCEL语法构建链
        # | 操作符将组件串联起来
        chain = (
            {
                "context": self.retriever | format_docs,  # 检索并格式化
                "question": RunnablePassthrough()          # 原样传递问题
            }
            | self.prompt           # 填充提示词模板
            | self.llm              # LLM生成
            | StrOutputParser()     # 解析输出为字符串
        )
        return chain

    def invoke(self, question: str) -> str:
        """
        执行问答

        Args:
            question: 用户问题

        Returns:
            AI回答
        """
        return self.chain.invoke(question)

    def stream(self, question: str):
        """
        流式输出问答

        Args:
            question: 用户问题

        Yields:
            回答片段
        """
        for chunk in self.chain.stream(question):
            yield chunk

    def get_retrieved_docs(self, question: str) -> List:
        """
        获取检索到的文档（用于调试）

        Args:
            question: 用户问题

        Returns:
            检索到的文档列表
        """
        return self.retriever.invoke(question)
```

### 4.7 步骤5：创建主程序

在项目根目录创建 `main.py`：

```python
"""
主程序 - 命令行入口

文件位置: main.py（项目根目录）

用法：
    python main.py build          # 构建知识库
    python main.py ask <问题>      # 提问
    python main.py chat           # 交互模式
"""
from src.config import Config
from src.document_processor import DocumentProcessor
from src.vectorstore import VectorStoreManager
from src.rag_chain import RAGChain
import sys


def print_usage():
    """打印用法"""
    print("""
用法:
    python main.py build          # 构建知识库
    python main.py ask <问题>      # 单次提问
    python main.py chat           # 交互模式

示例:
    python main.py build
    python main.py ask 什么是垃圾分类
    python main.py chat
""")


def build_knowledge_base():
    """构建知识库"""
    print("=" * 60)
    print("  环境小助手 - 知识库构建")
    print("=" * 60)

    # 步骤1: 处理文档
    print("\n【步骤1】处理文档")
    print("-" * 40)

    processor = DocumentProcessor(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    chunks = processor.process(Config.KNOWLEDGE_PATH)

    # 步骤2: 创建向量数据库
    print("\n【步骤2】创建向量数据库")
    print("-" * 40)

    vectorstore_manager = VectorStoreManager(
        persist_directory=Config.VECTOR_DB_PATH,
        api_key=Config.OPENAI_API_KEY,
        embedding_model=Config.EMBEDDING_MODEL
    )
    vectorstore_manager.create_from_documents(chunks)

    print("\n" + "=" * 60)
    print("  [OK] 知识库构建完成！")
    print("=" * 60)


def ask_question(question: str):
    """
    问答

    Args:
        question: 用户问题
    """
    print("=" * 60)
    print("  环境小助手 - 智能问答")
    print("=" * 60)

    # 加载向量数据库
    vectorstore_manager = VectorStoreManager(
        persist_directory=Config.VECTOR_DB_PATH,
        api_key=Config.OPENAI_API_KEY,
        embedding_model=Config.EMBEDDING_MODEL
    )
    retriever = vectorstore_manager.get_retriever(top_k=Config.RETRIEVE_TOP_K)

    # 创建RAG链
    rag_chain = RAGChain(
        retriever=retriever,
        model_name=Config.LLM_MODEL,
        api_key=Config.OPENAI_API_KEY,
    )

    # 显示检索结果
    print("\n【检索到的相关文档】")
    print("-" * 40)
    docs = rag_chain.get_retrieved_docs(question)
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知")
        print(f"\n文档{i} [来源: {source}]:")
        print(doc.page_content[:150] + "...")

    # 生成回答
    print("\n" + "=" * 60)
    print("【AI回答】")
    print("-" * 40)
    answer = rag_chain.invoke(question)
    print(answer)
    print("=" * 60)


def interactive_mode():
    """交互模式"""
    print("=" * 60)
    print("  环境小助手 - 交互模式")
    print("  输入 'quit' 或 'exit' 退出")
    print("=" * 60)

    # 初始化
    vectorstore_manager = VectorStoreManager(
        persist_directory=Config.VECTOR_DB_PATH,
        api_key=Config.OPENAI_API_KEY,
        embedding_model=Config.EMBEDDING_MODEL
    )
    retriever = vectorstore_manager.get_retriever(top_k=Config.RETRIEVE_TOP_K)

    rag_chain = RAGChain(
        retriever=retriever,
        model_name=Config.LLM_MODEL,
        api_key=Config.OPENAI_API_KEY,
    )

    while True:
        print("\n请输入问题:")
        question = input("> ").strip()

        if question.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        if not question:
            continue

        try:
            print("\n回答: ", end="")
            for chunk in rag_chain.stream(question):
                print(chunk, end="", flush=True)
            print()
        except Exception as e:
            print(f"\n错误: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "build":
            build_knowledge_base()
        elif command == "ask":
            question = " ".join(sys.argv[2:])
            if not question:
                question = "什么是垃圾分类？"
            ask_question(question)
        elif command == "chat":
            interactive_mode()
        else:
            print(f"未知命令: {command}")
            print_usage()
    else:
        print_usage()
```

### 4.8 运行测试

```bash
# 构建知识库
python main.py build

# 单次提问
python main.py ask 什么是垃圾分类

# 交互模式
python main.py chat
```

### 4.9 本阶段完成检查

- [ ] `src/config.py` 已创建
- [ ] `src/document_processor.py` 已创建
- [ ] `src/vectorstore.py` 已创建
- [ ] `src/rag_chain.py` 已创建
- [ ] `main.py` 已创建
- [ ] `python main.py build` 运行成功，生成 `chroma_db/` 目录
- [ ] `python main.py ask 什么是垃圾分类` 运行成功，返回正确答案

---

## 5. 第二阶段：优化与增强

### 5.1 本阶段目标

添加对话记忆、来源引用、混合检索等增强功能。

### 5.2 本阶段文件目录

**阶段结束时**：
```
project/
├── .env
├── requirements.txt
├── main.py
├── data/
│   └── knowledge/
├── chroma_db/
└── src/
    ├── __init__.py
    ├── config.py
    ├── document_processor.py
    ├── vectorstore.py
    ├── rag_chain.py
    └── advanced/                   # [新增] 进阶功能目录
        ├── __init__.py             # [新增]
        ├── conversational_rag.py   # [新增] 带记忆的RAG
        └── hybrid_retriever.py     # [新增] 混合检索
```

### 5.3 创建进阶功能目录

```bash
mkdir -p src/advanced
```

### 5.4 创建 src/advanced/__init__.py

```python
# src/advanced 包初始化文件
from .conversational_rag import ConversationalRAG
from .hybrid_retriever import create_hybrid_retriever
```

### 5.5 创建带记忆的RAG `src/advanced/conversational_rag.py`

```python
"""
带记忆的RAG问答

文件位置: src/advanced/conversational_rag.py

学习要点：
1. InMemoryChatMessageHistory 存储对话历史
2. RunnableWithMessageHistory 自动处理历史上下文
"""
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from typing import Dict


class ConversationalRAG:
    """带记忆的RAG问答"""

    PROMPT_TEMPLATE = """你是一个专业的环境小助手，请根据以下上下文信息和对话历史回答用户问题。
如果上下文中没有相关信息，请诚实地说"我没有找到相关信息"，不要编造答案。

上下文信息：
{context}

请回答用户问题："""

    def __init__(
        self,
        retriever,
        model_name: str = "qwen-plus",
        api_key: str = None,
    ):
        """初始化带记忆的RAG"""
        self.retriever = retriever
        self.llm = ChatTongyi(
            model_name=model_name,
            dashscope_api_key=api_key,
        )

        # 创建提示词模板（包含历史消息占位符）
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_TEMPLATE),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])

        # 会话存储
        self.store: Dict[str, InMemoryChatMessageHistory] = {}

        # 构建链
        self.chain = self._build_chain()

    def _get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        """获取或创建会话历史"""
        if session_id not in self.store:
            self.store[session_id] = InMemoryChatMessageHistory()
        return self.store[session_id]

    def _build_chain(self):
        """构建带记忆的RAG链"""
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # 基础链
        base_chain = (
            {
                "context": self.retriever | format_docs,
                "question": RunnablePassthrough(),
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

        # 包装为带记忆的链
        chain_with_history = RunnableWithMessageHistory(
            base_chain,
            self._get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )

        return chain_with_history

    def chat(self, question: str, session_id: str = "default") -> str:
        """
        对话

        Args:
            question: 用户问题
            session_id: 会话ID

        Returns:
            AI回答
        """
        config = {"configurable": {"session_id": session_id}}
        return self.chain.invoke(question, config)

    def clear_history(self, session_id: str = "default"):
        """清空指定会话的历史"""
        if session_id in self.store:
            self.store[session_id].clear()
```

### 5.6 创建混合检索 `src/advanced/hybrid_retriever.py`

```python
"""
混合检索 - 结合BM25关键词检索和向量检索

文件位置: src/advanced/hybrid_retriever.py

学习要点：
1. BM25Retriever 基于关键词匹配
2. EnsembleRetriever 组合多个检索器
3. weights 参数控制各检索器的权重
"""
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from typing import List


def create_hybrid_retriever(
    documents: List[Document],
    vectorstore,
    top_k: int = 3,
    weights: List[float] = [0.5, 0.5]
):
    """
    创建混合检索器

    Args:
        documents: 文档列表（用于BM25）
        vectorstore: 向量存储
        top_k: 返回文档数量
        weights: [BM25权重, 向量检索权重]

    Returns:
        混合检索器
    """
    # BM25关键词检索
    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = top_k

    # 向量检索
    vector_retriever = vectorstore.as_retriever(
        search_kwargs={"k": top_k}
    )

    # 组合检索器
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=weights
    )

    return ensemble_retriever
```

### 5.7 本阶段完成检查

- [ ] `src/advanced/` 目录已创建
- [ ] `src/advanced/__init__.py` 已创建
- [ ] `src/advanced/conversational_rag.py` 已创建
- [ ] `src/advanced/hybrid_retriever.py` 已创建

---

## 6. 第三阶段：Flask API封装

### 6.1 本阶段目标

将RAG功能封装为RESTful API服务。

### 6.2 本阶段文件目录

**阶段结束时**：
```
project/
├── .env
├── requirements.txt
├── main.py
├── app.py                        # [新增] Flask API服务
├── data/
│   └── knowledge/
├── chroma_db/
└── src/
    ├── __init__.py
    ├── config.py
    ├── document_processor.py
    ├── vectorstore.py
    ├── rag_chain.py
    └── advanced/
        ├── __init__.py
        ├── conversational_rag.py
        └── hybrid_retriever.py
```

### 6.3 创建Flask应用 `app.py`

在项目根目录创建 `app.py`：

```python
"""
Flask API服务

文件位置: app.py（项目根目录）

启动方式：
    python app.py

接口：
    GET  /health         - 健康检查
    POST /api/chat       - 问答
    POST /api/chat/stream - 流式问答
    POST /api/rebuild    - 重建知识库
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv

from src.config import Config
from src.document_processor import DocumentProcessor
from src.vectorstore import VectorStoreManager
from src.rag_chain import RAGChain

load_dotenv()

app = Flask(__name__)
CORS(app)

# 全局变量
rag_chain = None
vectorstore_manager = None


def init_rag():
    """初始化RAG组件"""
    global rag_chain, vectorstore_manager

    # 检查向量数据库是否存在
    if not os.path.exists(Config.VECTOR_DB_PATH):
        raise RuntimeError(
            "向量数据库不存在，请先运行 python main.py build 构建知识库"
        )

    # 加载向量数据库
    vectorstore_manager = VectorStoreManager(
        persist_directory=Config.VECTOR_DB_PATH,
        api_key=Config.OPENAI_API_KEY,
        embedding_model=Config.EMBEDDING_MODEL
    )
    retriever = vectorstore_manager.get_retriever(top_k=Config.RETRIEVE_TOP_K)

    # 创建RAG链
    rag_chain = RAGChain(
        retriever=retriever,
        model_name=Config.LLM_MODEL,
        api_key=Config.OPENAI_API_KEY,
    )

    print("RAG组件初始化完成")


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "model": Config.LLM_MODEL
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    问答接口

    请求体：
        {
            "question": "你的问题"
        }

    响应：
        {
            "question": "问题",
            "answer": "回答",
            "sources": [...]
        }
    """
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    try:
        # 获取检索的文档
        docs = rag_chain.get_retrieved_docs(question)

        # 生成回答
        answer = rag_chain.invoke(question)

        # 构建响应
        sources = [
            {
                "content": doc.page_content[:200],
                "source": doc.metadata.get("source", "未知"),
                "page": doc.metadata.get("page", "")
            }
            for doc in docs
        ]

        return jsonify({
            "question": question,
            "answer": answer,
            "sources": sources
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """
    流式问答接口

    使用 Server-Sent Events (SSE) 实现流式输出
    """
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    def generate():
        try:
            for chunk in rag_chain.stream(question):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream'
    )


@app.route('/api/rebuild', methods=['POST'])
def rebuild_knowledge():
    """
    重建知识库接口

    响应：
        {
            "status": "success",
            "message": "知识库重建完成",
            "chunks": 100
        }
    """
    try:
        # 处理文档
        processor = DocumentProcessor(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        chunks = processor.process(Config.KNOWLEDGE_PATH)

        # 创建向量数据库
        global vectorstore_manager
        vectorstore_manager = VectorStoreManager(
            persist_directory=Config.VECTOR_DB_PATH,
            api_key=Config.OPENAI_API_KEY,
            embedding_model=Config.EMBEDDING_MODEL
        )
        vectorstore_manager.create_from_documents(chunks)

        # 重新初始化
        init_rag()

        return jsonify({
            "status": "success",
            "message": "知识库重建完成",
            "chunks": len(chunks)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("  环境小助手 - Flask API服务")
    print("=" * 60)

    init_rag()

    print("\n服务启动中...")
    print(f"API地址: http://localhost:5000")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 6.4 API使用示例

```bash
# 健康检查
curl http://localhost:5000/health

# 问答
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"什么是垃圾分类？\"}"

# 流式问答
curl -X POST http://localhost:5000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"什么是垃圾分类？\"}"

# 重建知识库
curl -X POST http://localhost:5000/api/rebuild
```

### 6.5 本阶段完成检查

- [ ] `app.py` 已创建
- [ ] `python app.py` 启动成功
- [ ] `curl http://localhost:5000/health` 返回正常
- [ ] POST `/api/chat` 接口工作正常

---

## 7. 第四阶段：进阶功能

### 7.1 本阶段目标

添加日志记录、请求限流等生产级功能。

### 7.2 本阶段文件目录

**阶段结束时**：
```
project/
├── .env
├── requirements.txt
├── main.py
├── app.py
├── logs/                         # [新增] 日志目录
│   └── app.log                   # [自动生成]
├── data/
│   └── knowledge/
├── chroma_db/
└── src/
    ├── __init__.py
    ├── config.py
    ├── document_processor.py
    ├── vectorstore.py
    ├── rag_chain.py
    └── advanced/
        ├── __init__.py
        ├── conversational_rag.py
        └── hybrid_retriever.py
```

### 7.3 添加日志记录

在 `app.py` 中添加：

```python
import logging
from datetime import datetime

# 创建日志目录
os.makedirs("logs", exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/app.log'
)
logger = logging.getLogger(__name__)


@app.route('/api/chat', methods=['POST'])
def chat():
    start_time = datetime.now()
    # ... 原有逻辑 ...

    # 记录日志
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"问题: {question[:50]}... | 耗时: {duration:.2f}秒")

    return jsonify(response)
```

### 7.4 添加请求限流

安装依赖：
```bash
pip install flask-limiter
```

在 `app.py` 中添加：
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    # ...
```

---

## 8. 常见问题与解决方案

### Q1: 如何选择合适的chunk_size？

| 文档类型 | 建议chunk_size | 说明 |
|---------|---------------|------|
| FAQ、短文章 | 200-500 | 问答对完整性好 |
| 技术文档 | 500-1000 | 保持段落完整 |
| 书籍、报告 | 1000-2000 | 保留更多上下文 |

**建议**：overlap 设为 chunk_size 的 10%

### Q2: 如何提高检索精度？

1. **调整分割参数**：优化 chunk_size 和 overlap
2. **混合检索**：结合 BM25 和向量检索
3. **重排序**：添加 Rerank 模型
4. **优化提示词**：让模型更好理解上下文

### Q3: Qwen API 报错怎么办？

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| Invalid API Key | API Key 错误 | 检查 .env 文件配置 |
| Rate limit | 请求频率过高 | 添加重试机制或降低频率 |
| Model not found | 模型名称错误 | 使用正确的模型名如 qwen-plus |

### Q4: 为什么使用 DashScopeEmbeddings 和 ChatTongyi？

| 组件 | OpenAI兼容方式 | 阿里云官方集成 |
|------|---------------|---------------|
| Embeddings | OpenAIEmbeddings | DashScopeEmbeddings |
| LLM | ChatOpenAI | ChatTongyi |
| **优点** | 通用性强 | 无需tiktoken/无SSL问题 |
| **缺点** | 需要网络下载tiktoken | 仅限阿里云 |

**推荐**：在阿里云环境下使用官方集成更稳定。

### Q5: 如何调试检索结果？

```python
# 查看检索到的文档
docs = rag_chain.get_retrieved_docs(question)
for doc in docs:
    print(f"来源: {doc.metadata.get('source')}")
    print(f"内容: {doc.page_content}")
    print("-" * 40)
```

---

## 开发顺序建议

| 阶段 | 时间 | 内容 |
|------|------|------|
| 第1天 | 2小时 | 环境搭建 + 理解核心概念 |
| 第2天 | 3小时 | 实现基础RAG（第一阶段） |
| 第3天 | 2小时 | 优化与增强（第二阶段） |
| 第4天 | 2小时 | Flask API封装（第三阶段） |
| 第5天 | 2小时 | 进阶功能（第四阶段） |
| 第6天 | 1小时 | 测试与文档完善 |

---

## 学习资源

- [LangChain官方文档](https://python.langchain.com/docs/get_started/introduction)
- [LangChain中文教程](https://www.langchain.com.cn/)
- [通义千问API文档](https://help.aliyun.com/zh/dashscope/)
- [RAG最佳实践](https://blog.langchain.dev/deconstructing-rag/)

---

**祝学习顺利！有问题随时问我。**