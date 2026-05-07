from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from typing import Dict

"""
带记忆的RAG问答

文件位置: src/advanced/conversational_rag.py

学习要点：
1. InMemoryChatMessageHistory 存储对话历史
2. RunnableWithMessageHistory 自动处理历史上下文
"""

class ConversationalRAG:
    """带记忆的RAG问答"""

    PROMPT_TEMPLATE = """你是一个专业的环境小助手，请根据以下上下文信息和对话历史回答用户问题。
    如果上下文中没有相关信息，请诚实地说"我没有找到相关信息"，不要编造答案。
    
    上下文信息：
    {context}
    
    请回答用户问题："""

    def __init__(self,
         retriever,
         model_name:str="qwen-plus",
         api_key:str=None
    ):
        """初始化带记忆的RAG"""
        self.retriever=retriever
        self.llm=ChatTongyi(
            model_name=model_name,
            dashscope_api_key=api_key,
        )

        # 创建提示词模板（包含历史消息占位符）
        self.prompt=ChatPromptTemplate.from_messages([
            ("system",self.PROMPT_TEMPLATE),
            MessagesPlaceholder(variable_name="chat_history"),# 历史消息占位符
            ("human","{question}")
        ])
        # 会话存储
        self.store:Dict[str,InMemoryChatMessageHistory]={}
        # 构建链
        self.chain=self._build_chain()

    def _get_session_history(self,session_id:str)->InMemoryChatMessageHistory:
        """获取或创建会话历史"""
        if session_id not  in self.store:
            self.store[session_id]=InMemoryChatMessageHistory()
        return self.store[session_id]

    def _build_chain(self):
        """构建带记忆的RAG链"""
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # 基础链
        base_chain=(
            {
                "context":self.retriever | format_docs(),
                "question":RunnablePassthrough(),
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        # 包装为带记忆的链
        chain_with_history=RunnableWithMessageHistory(
            base_chain,
            self._get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )
        return chain_with_history

    def chat(self,question:str,session_id:str="default")->str:
        """
       对话

       Args:
           question: 用户问题
           session_id: 会话ID

       Returns:
           AI回答
       """
        config={"configurable":{"session_id":session_id}}
        return self.chain.invoke(question,config=config)

    def clear_history(self,session_id:str="default"):
        """清空指定会话的历史"""
        if session_id in self.store:
            self.store[session_id].clear()


































