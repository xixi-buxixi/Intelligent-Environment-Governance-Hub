from src.config import Config
from src.document_processor import DocumentProcessor
from src.vectorstore import VectorStoreManager
from src.rag_chain import RAGChain
import sys
from src.services.assistant_service import AssistantService


"""
主程序 - 命令行入口

用法：
    python main.py build          # 构建知识库
    python main.py ask <问题>      # 提问
    python main.py chat           # 交互模式
    python main.py ask "xxx" agent
    python main.py ask "xxx" hybrid
"""


def print_usage():
    """打印用法"""
    print("""
    用法:
        python main.py build                    # 构建知识库
        python main.py ask <问题> [模式]         # 单次提问 (模式可选: rag, agent, hybrid)
        python main.py chat                     # 交互模式

    示例:
        python main.py build
        python main.py ask 什么是垃圾分类
        python main.py ask 什么是垃圾分类 agent
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

    processor=DocumentProcessor(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )

    chunks=processor.process(Config.KNOWLEDGE_PATH)

    # 步骤2: 创建向量数据库
    print("\n【步骤2】创建向量数据库")
    print("-" * 40)

    vectorstore_manager=VectorStoreManager(
        persist_directory=Config.VECTOR_DB_PATH,
        api_key=Config.OPENAI_API_KEY,
        embedding_model=Config.EMBEDDING_MODEL
    )
    vectorstore_manager.create_from_documents(chunks)

    print("\n" + "=" * 60)
    print("  [OK] 知识库构建完成！")
    print("=" * 60)

def ask_question(question:str,mode: str = "rag"):
    """
    问答

    Args:
        question: 用户问题
    """
    service=AssistantService()
    result=service.ask(question,mode=mode)
    print(result["answer"])

def interactive_mode():
    """交互模式"""
    print("=" * 60)
    print("  环境小助手 - 交互模式")
    print("  输入 'quit' 或 'exit' 退出")
    print("=" * 60)

    #初始化
    vectorstore_manager=VectorStoreManager(
        persist_directory=Config.VECTOR_DB_PATH,
        api_key=Config.OPENAI_API_KEY,
        embedding_model=Config.EMBEDDING_MODEL
    )
    retriever=vectorstore_manager.get_retriever(top_k=Config.RETRIEVE_TOP_K)

    rag_chain=RAGChain(
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
    if len(sys.argv)>1:
        command=sys.argv[1]
        if command=="build":
            build_knowledge_base()
        elif command=="ask":
            if len(sys.argv)>2:
                question=sys.argv[2]
                # 获取模式参数，默认为 rag
                mode = sys.argv[3] if len(sys.argv) > 3 else "rag"
                ask_question(question, mode=mode)
            else:
                print("请输入问题")
        elif command=="chat":
            interactive_mode()
        else:
            print_usage()
    else:
        print_usage()



















