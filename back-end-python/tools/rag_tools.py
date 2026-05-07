"""
RAG相关工具
"""

from langchain_core.tools import tool
from src.rag_chain import RAGChain
from src.vectorstore import VectorStoreManager
from src.config import Config
import threading
import time
from src.document_processor import DocumentProcessor
import os

# 执行锁（防止并发重建）
_rebuild_lock = threading.Lock()


@tool
def rag_qa(question:str)->dict:
    """
    知识库问答工具。从环保知识库中检索答案。

    使用场景：
    - 用户询问环保相关知识时
    - 用户需要从知识库获取信息时

    Args:
        question: 用户问题

    Returns:
        dict: 包含answer和sources
    """
    try:
        manager=VectorStoreManager(
            persist_directory=Config.VECTOR_DB_PATH,
            api_key=Config.OPENAI_API_KEY,
            embedding_model=Config.EMBEDDING_MODEL,
        )
        retriever=manager.get_retriever(top_k=Config.RETRIEVE_TOP_K)

        rag_chain=RAGChain(
            retriever=retriever, # 向量检索器
            model_name=Config.LLM_MODEL,
            api_key=Config.OPENAI_API_KEY,
        )
        docs=rag_chain.get_retrieved_docs(question)
        answer=rag_chain.invoke(question)

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
def rag_rebuild()->dict:
    """
   知识库重建工具。重新加载所有知识文档。

   使用场景：
   - 知识库文档更新后需要重建
   - 用户要求重新导入文档

   注意：这是高成本操作，需要用户确认。

   Returns:
       dict: 包含重建结果和耗时
   """

    if not _rebuild_lock.acquire(blocking=False):
        return {"ok": False, "data": None, "error": "重建正在进行中，请稍后再试。"}

    try:
        start_time=time.time()
        processor=DocumentProcessor(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        chunks=processor.process(Config.KNOWLEDGE_PATH)

        manager=VectorStoreManager(
            persist_directory=Config.VECTOR_DB_PATH,
            api_key=Config.OPENAI_API_KEY,
            embedding_model=Config.EMBEDDING_MODEL
        )
        manager.create_from_documents(chunks)

        elapsed=time.time() - start_time
        return {
            "ok": True,
            "data": {"elapsed_seconds": elapsed, "message": "知识库重建完成"},
            "error": None
        }
    except Exception as e:
        return {"ok": False, "data": None, "error": f"重建失败: {e}"}
    finally:
        _rebuild_lock.release()

@tool
def system_health()->dict:
    """
   系统健康检查工具。

   使用场景：
   - 用户询问系统状态
   - 排错时需要检查系统

   Returns:
       dict: 系统状态信息
   """
    try:
        status={
            "api_key_set": bool(Config.OPENAI_API_KEY),
            "knowledge_dir_exists": os.path.exists(Config.KNOWLEDGE_PATH),
            "chroma_db_exists": os.path.exists(Config.VECTOR_DB_PATH),
        }
        all_ok = all(status.values())
        return {
                    "ok": all_ok,
                    "data": status,
                    "error": None if all_ok else "部分组件异常"
                }
    except Exception as e:
        return {"ok": False, "data": None, "error": f"检查失败: {e}"}





























