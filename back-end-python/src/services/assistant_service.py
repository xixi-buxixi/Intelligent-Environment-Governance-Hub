from src.config import Config
from src.vectorstore import VectorStoreManager
from src.rag_chain import RAGChain
from src.complete_agent import CompleteAdvancedAgent
from src.llm.factory import get_chat_model


class AssistantService:
    def __init__(self, rag_chain=None):
        self._agent = CompleteAdvancedAgent(
            max_history=Config.AGENT_MAX_HISTORY,
            max_iterations=Config.AGENT_MAX_ITERATIONS,
            max_retries=Config.AGENT_MAX_RETRIES,
            enable_reflection=Config.AGENT_ENABLE_REFLECTION,
            state_dir=Config.AGENT_STATE_DIR,
        )
        self._rag_chain = rag_chain  # 支持外部注入

    def _get_rag_chain(self):
        if self._rag_chain is None:
            manager=VectorStoreManager(
                persist_directory=Config.VECTOR_DB_PATH,
                api_key=Config.OPENAI_API_KEY,
                embedding_model=Config.EMBEDDING_MODEL,
            )
            retriever=manager.get_retriever(top_k=Config.RETRIEVE_TOP_K)
            self._rag_chain=RAGChain(
                retriever=retriever,
                model_name=Config.LLM_MODEL,
                api_key=Config.OPENAI_API_KEY,
            )
        return self._rag_chain

    def ask(self,question:str,mode:str="rag")->dict:
        mode=mode.lower()
        if mode == "agent":
            result = self._agent.chat(question)
            answer = (result.get("answer") or "").strip()
            # Agent 失败时自动降级到 RAG，避免前端出现“请求成功但无可展示内容”
            if (not answer) or ("多次尝试后仍无法完成请求" in answer):
                rag_answer = self._get_rag_chain().invoke(question)
                return {
                    "mode": "agent-fallback-rag",
                    "answer": rag_answer,
                    "meta": {"agent": result, "fallback": "rag"},
                }
            return {"mode": "agent", "answer": answer, "meta": result}
        if mode=="hybrid":
            agent_result=self._agent.chat(question)
            if agent_result.get("answer"):
                return {"mode": "hybrid-agent", "answer": agent_result["answer"], "meta": agent_result}
            rag_answer=self._get_rag_chain().invoke(question)
            return {"mode": "hybrid-rag", "answer": rag_answer, "meta": {}}
        if mode == "direct":
            # 直接调用 LLM，不使用知识库
            llm = get_chat_model()
            answer = llm.invoke(question).content
            return {"mode": "direct", "answer": answer, "meta": {}}
        rag = self._get_rag_chain()
        return {"mode": "rag", "answer": rag.invoke(question), "meta": {}}











