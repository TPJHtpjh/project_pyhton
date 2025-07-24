from langchain.docstore.document import Document
#from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, CSVLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.llms import Ollama
from RAG import embedding
#from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import shutil
import random
import sys
import io
import re
'''
此文件依旧是创建或者更新RAG数据库才运行一次
'''

#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
QUESTION_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "question_db")
# embedding=OllamaEmbeddings(
#         model="bge-m3",#bge-m3没有的话换成下面的
#         #model='nomic-embed-text'
#         base_url="http://localhost:8080"
# )

# llm=Ollama(model="deepseek-r1:7b",
#   base_url="http://localhost:8080",
#   num_gpu=30
#   # ,num_predict=40960
# )
def cleanup_question_db():
    if os.path.exists(QUESTION_DB_DIR):
        shutil.rmtree(QUESTION_DB_DIR)
        print("已清理原有向量数据库目录：", QUESTION_DB_DIR)

def load_file_excel(file_path):
    docs=[]
    if file_path:
        excel_loader=DirectoryLoader(
            path=file_path,glob='**/*.csv',
            loader_cls=CSVLoader,
            loader_kwargs={'encoding':'utf-8'}
        )
        docs=excel_loader.load()
    else:
        print('请输入文件路径')
    print(f'成功加载了{len(docs)}个文档')
    return docs



def create_vectorstore(docs):
    if docs is None:
        print('无可用文档')
        return None
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=['\n\n','\n','，']
    )
    
    chunks=splitter.split_documents(docs)
    question_vectorstore=Chroma.from_documents(
        chunks,
        embedding,
        persist_directory=QUESTION_DB_DIR
    )
    return question_vectorstore



    
'''下面的参数需要改为,储存着题目的excel(.csv后缀)文件,的文件目录'''
questions=load_file_excel(r'D:\下载\one')
'''questions是list[Document]类型,一共有656个Document类的question元素。
  中0-148填空,149-346选择,347-655判断
  每一个Document元素都包括
  question.page_content:str   #没有分割的原始数据。包括题目，答案和难度.
  和question.metadata: dict      #元数据字典，记录数据来源。应该用不到。
'''
splitter=RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=['\n\n','\n','，']
    )
chunks=splitter.split_documents(questions)


if __name__=="__main__":
    cleanup_question_db()
    # for i,question in enumerate(questions):
    #     page_content=question.page_content
    #     #content=question
    #     if i in[148,149,150,346,347,348,655,656,657]:
    #      print(question.page_content+'\n')
    
    
    # for i,chunk in enumerate(chunks):
    #   if i<100:
    #     print(chunk)
    question_vectorstore=create_vectorstore(questions)
    if question_vectorstore is not None and hasattr(question_vectorstore,'persist'):
       #question_vectorstore.persist()
       print(f'questions已保存到本地{QUESTION_DB_DIR}')
    else:
        print('向量数据库未能保存')
# # 从文档创建集合
# vector_store = Chroma.from_documents(
# documents=split_docs,
# embedding=embeddings,
# persist_directory="./chroma_db",
# collection_metadata={"hnsw:space": "cosine"}
# )

# #相似性搜索
# results = vector_store.similarity_search(
# query="什么是向量数据库?",
# k=5,
# filter={"source": "guide.pdf"} # 元数据过滤
# )
# import chromadb
# # 连接到现有集合
# client = chromadb.PersistentClient(path="./chroma_db")
# collection = client.get_collection(name="langchain")
# # 打印数据结构
# print(f"集合中的条目数: {collection.count()}")
# # 获取所有记录
# records = collection.get(
# include=["embeddings", "documents", "metadatas"]
# )
#records:list[Document]
#'ids','embeddings','documents','metadatas'

