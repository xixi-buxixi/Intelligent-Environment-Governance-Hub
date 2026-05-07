from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from typing import List


"""
混合检索 - 结合BM25关键词检索和向量检索

文件位置: src/advanced/hybrid_retriever.py

学习要点：
1. BM25Retriever 基于关键词匹配
2. EnsembleRetriever 组合多个检索器
3. weights 参数控制各检索器的权重
"""


def create_hybrid_retriever(
        documents:List[Document],
        vectorstore,
        top_k:int=3,
        weights:List[float]=[0.5,0.5]
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
    bm25_retriever=BM25Retriever.from_documents(documents)
    bm25_retriever.k=top_k

    vector_retriever=vectorstore.as_retriever(
        search_kwargs={"k":top_k}
    )

    ensemble_retriever=EnsembleRetriever(
        retriever=[bm25_retriever,vector_retriever],
        weights=weights
    )

    return ensemble_retriever


















