from src.llm.factory import get_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import List



"""
RAG问答链 - 构建检索增强生成链

学习要点：
1. PromptTemplate定义提示词模板
2. RunnablePassthrough传递原始问题
3. | 操作符连接组件形成处理链（LCEL语法）
4. StrOutputParser将LLM输出转为字符串
5. 这就是LangChain Expression Language (LCEL)的核心用法
"""


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
            model_name:str="qwen-turbo",
            temperature:float=0.7,
            api_key:str=None,
    ):
        """
        初始化RAG链

        Args:
            retriever: 检索器
            model_name: 模型名称
            temperature: 温度参数
            api_key: API密钥
        """

        self.retriever=retriever

        # 使用 ChatTongyi（阿里云通义千问官方 LangChain 集成）
        print(f"初始化LLM：{model_name}")
        self.llm = get_chat_model(temperature=temperature)

        # 创建提示词模板
        self.prompt=ChatPromptTemplate.from_template(self.PROMPT_TEMPLATE)

        # 构建RAG链
        self.chain=self._build_chain()


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
        chain=(
            {
                "context":self.retriever|format_docs,# 检索并格式化
                "question":RunnablePassthrough()# 原样传递问题
            }
            | self.prompt# 填充提示词模板
            | self.llm# LLM生成
            | StrOutputParser()# 解析输出为字符串
        )
        return chain
    def invoke(self,question:str)->str:
        """
       执行问答

       Args:
           question: 用户问题

       Returns:
           AI回答
       """
        return self.chain.invoke(question)

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

    def get_retrieved_docs(self,question:str)->List:
        """
        获取检索到的文档（用于调试）

        Args:
            question: 用户问题

        Returns:
            检索到的文档列表
        """

        return self.retriever.invoke(question)





