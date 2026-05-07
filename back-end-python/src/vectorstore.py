from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import DashScopeEmbeddings
from typing import List, Optional
import os

"""
向量存储管理器 - 创建和管理向量数据库

学习要点：
1. Embeddings将文本转换为向量表示
2. VectorStore存储向量并支持相似度搜索
3. Chroma是轻量级本地向量数据库，适合学习
4. Retriever是VectorStore的检索接口
"""

class VectorStoreManager:
    """向量存储管理器：创建和管理向量数据库"""

    def __init__(
            self,
            persist_directory: str,
            api_key: str,
            embedding_model: str = "text-embedding-v4",
    ):
        """
        初始化向量存储管理器

        Args:
            persist_directory: 向量数据库持久化目录
            api_key: API密钥
            api_base: API基础URL（DashScopeEmbeddings不需要）
            embedding_model: 嵌入模型名称
        """
        self.persist_directory = persist_directory
        self.api_key = api_key
        self.embedding_model = embedding_model

        # 使用 DashScopeEmbeddings（阿里云通义千问官方嵌入模型，无需 tiktoken）
        self.embeddings = DashScopeEmbeddings(
            model=embedding_model,
            dashscope_api_key=api_key,
        )
        self.vectorstore: Optional[Chroma] = None

    def create_from_documents(self,documents:List[Document])->Chroma:
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

        self.vectorstore=Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
        )
        print(f"向量数据库创建完成，保存至: {self.persist_directory}")
        return self.vectorstore

    def load(self)->Chroma:
        """
        加载已有向量存储

        Returns:
            向量存储实例
        """
        if not os.path.exists(self.persist_directory):
            raise ValueError(f"向量数据库不存在: {self.persist_directory}")

        print(f"正在加载向量数据库:{self.persist_directory}")

        self.vectorstore=Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )
        return self.vectorstore


    def get_retriever(self,top_k:int=3):
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

    def similarity_search(self,query:str,k:int=3)->List[Document]:
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

        return self.vectorstore.similarity_search(query,k=k)


