from langchain.docstore.document import Document
# from langchain.vectorstores import FAISS
from pydantic import SecretStr
from langchain_community.document_loaders import DirectoryLoader, WebBaseLoader, PyPDFLoader, TextLoader, Docx2txtLoader, CSVLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
import os
import pymysql
import pymysql.cursors
import shutil
import sys
import io
from langchain_community.llms import Ollama
'''
更新RAG数据库运行一次RAG.py文件
'''
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
vectorstore=None
embedding = OllamaEmbeddings(
        #model="nomic-embed-text", #本地语义模型
        model='bge-m3',#这个效果更好
        base_url="http://localhost:8080",
        num_thread=8
    )


llm=Ollama(model="deepseek-r1:7b",
base_url="http://localhost:8080",
num_gpu=30
# ,num_predict=40960
)
# llm = ChatTongyi(model="qwen-turbo", api_key=SecretStr("sk-1c9ecdbc37244d809ce41861a47b4e76"))
#llm=DeepSeekChat(model_name="deepseek-chat",api_key="") DeepSeek模型

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',      # <-- 修改为您的MySQL用户名
    'password': '', # <-- 修改为您的MySQL密码
    'db': '',      # <-- 您希望使用的数据库名称
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
def get_db_connection():
    try:
        # 先连接到MySQL服务器，不指定数据库
        server_conn_config = {k: v for k, v in DB_CONFIG.items() if k not in ['db', 'cursorclass']}
        server_conn = pymysql.connect(**server_conn_config)
        
        with server_conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['db']} CHARACTER SET utf8mb4")
            print(f"数据库 '{DB_CONFIG['db']}' 已准备就绪。")
        
        server_conn.close()

        # 连接到指定数据库
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.Error as e:
        print(f"数据库连接失败: {e}")
        return None
def load_documents_from_db(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT content,source FROM documents")
            docs=[Document(page_content=row['content'],metadata={'source':row['source']}) for row in cursor.fetchall()]
            print(f"成功从MySQL加载{len(docs)}条文档")
            return docs
    except pymysql.err.ProgrammingError as e:
        if e.args[0] == 1146: # Error code for "Table... doesn't exist"
            print("数据库 'documents' 表不存在，将跳过从数据库加载。")
            return []
        else:
            # For other database errors, print the error and re-raise
            print(f"数据库查询出错: {e}")
            raise

def cleanup_chroma_db():
    if os.path.exists(CHROMA_DB_DIR):
        shutil.rmtree(CHROMA_DB_DIR)
        print("已清理向量数据库目录：", CHROMA_DB_DIR)

def load_file_url_documents(file_path=None, url=None):#从本地文件和URL加载文档
    docs = []
    if file_path:
        if os.path.isfile(file_path):
            # 单文件
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
                docs.extend(loader.load())
            elif ext == ".txt":
                loader = TextLoader(file_path, encoding="utf-8")
                docs.extend(loader.load())
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
                docs.extend(loader.load())
            elif ext == ".csv":
                loader = CSVLoader(file_path, encoding="utf-8")
                docs.extend(loader.load())
        else:
            # 文件夹，批量加载
            for root, _, files in os.walk(file_path):
                for file in files:
                    try:
                        full_path = os.path.join(root, file)
                        ext = os.path.splitext(file)[1].lower()
                        if ext == ".pdf":
                            loader = PyPDFLoader(full_path)
                        elif ext == ".txt":
                            loader = TextLoader(full_path, encoding="utf-8")
                        elif ext == ".docx":
                            loader = Docx2txtLoader(full_path)
                        elif ext == ".csv":
                            loader = CSVLoader(full_path, encoding="utf-8")
                        docs.extend(loader.load())
                        print(f"成功加载文件 {file}")
                    except Exception as e:
                        print(f"加载文件 {file} 时出错: {e}")
                        continue
                    
    if url:
        web_loader = WebBaseLoader(url)
        docs.extend(web_loader.load())
        
    print(f"从文件/URL加载了 {len(docs)} 个文档。")
    return docs

def create_chunks(docs):#创建RAG向量数据库
    if not docs:
        print("没有可用于创建向量数据库的文档。")
        # return None
        return []

    print(f"正在为 {len(docs)} 个文档创建向量存储...")
    
    doc_spliter = SemanticChunker(embeddings=embedding, add_start_index=True)
    chunks = doc_spliter.split_documents(docs)
    return chunks
def create_vectorstore(chunks):
    vectorstore = Chroma.from_documents(chunks, embedding, persist_directory=CHROMA_DB_DIR)
    print("向量存储创建完毕。")
    return vectorstore
def add_to_vectorstore(vectorstore,file_path):
    file=load_file_url_documents(file_path=file_path, url=None)
    file_chunk=create_chunks(file)
    vectorstore.add_documents(file_chunk)
    vectorstore.persist()
    return vectorstore




if __name__== "__main__":
    file_docs = load_file_url_documents(file_path=r"D:\下载\one", url=None)
    chunks=create_chunks(file_docs)
    # 需要更新RAG数据库时才运行此文件
    cleanup_chroma_db()#清理创建的Chroma DB，
    # 1. 从数据库加载文档
    # conn = get_db_connection()
    # db_docs = []
    # if conn:
    #     try:
    #         db_docs = load_documents_from_db(conn)
    #     finally:
    #         conn.close()

    # 2. 从本地文件和URL加载文档 (请根据需要修改路径和URL)
    # 示例: file_path="your_folder", url="http://example.com"
    

    # 3. 合并所有文档源
    # all_docs = db_docs + file_docs
    
    if not file_docs:
        print("未能从任何来源加载到文档，程序退出。")
    else:
        # 4. 基于所有文档创建向量数据库
        vectorstore= create_vectorstore(chunks)
        # 5. 保存向量数据库
        if vectorstore is not None :
            #vectorstore.persist()
            print(f"向量数据库已保存到本地{CHROMA_DB_DIR}.")
        else:
            print("向量数据库未能保存。")