from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
import os
from src.config import Config



"""
文档处理器 - 加载和分割文档

学习要点：
1. Document是LangChain的基本数据单元
2. DocumentLoader负责从各种来源加载文档
3. TextSplitter将长文档分割成适合检索的小块
4. chunk_overlap确保上下文连续性
"""
class DocumentProcessor:
    """文档处理器：加载和分割文档"""

    def __init__(self,chunk_size:int=500,chunk_overlap:int=50):
        self.chunk_size=Config.CHUNK_SIZE
        self.chunk_overlap=Config.CHUNK_OVERLAP

        # 创建文本分割器
        # 中文优化分隔符：优先按段落、句子分割
        self.text_splitter=RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=Config.SEPARATORS
        )

    def load_pdf(self,file_path:str)->List[Document]:
        """加载PDF文件"""
        loader=PyPDFLoader(file_path)
        return loader.load()

    def load_text(self,file_path:str)->List[Document]:
        """加载文本文件"""
        loader=TextLoader(file_path,encoding="utf-8")
        return loader.load()
    def load_directory(self,dir_path:str)->List[Document]:
        """加载目录下所有文档"""
        documents=[]

        # 遍历目录
        for root,dirs,files in os.walk(dir_path):
            for file in files:
                file_path=os.path.join(root,file)
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

    def split_documents(self,documents:List[Document])->List[Document]:
        """分割文档为小块"""
        return self.text_splitter.split_documents(documents)

    def process(self,source_path:str)->List[Document]:
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
            documents=self.load_directory(source_path)
        elif os.path.isfile(source_path):
            if source_path.endswith('.pdf'):
                documents=self.load_pdf(source_path)
            else:
                documents=self.load_text(source_path)
        else:
            raise ValueError(f"路径不存在: {source_path}")

        print(f"加载了 {len(documents)} 个文档片段")

        chunks=self.split_documents(documents)
        print(f"分割成 {len(chunks)} 个文本块")

        return chunks

