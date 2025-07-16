from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, DirectoryLoader, TextLoader, PyPDFDirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
import os
import pymysql
import pymysql.cursors
import shutil
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
vectorstore=None
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
            loader_map = {
                ".txt": TextLoader(file_path, encoding="utf-8"),
                ".pdf": PyPDFLoader(file_path),
            }
            ext = os.path.splitext(file_path)[1].lower()
            loader = loader_map.get(ext)
            if loader:
                docs.extend(loader.load())
        else:
            # 文件夹，批量加载
            pdf_loader = PyPDFDirectoryLoader(file_path, glob="**/*.pdf")
            txt_loader = DirectoryLoader(file_path, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}, use_multithreading=True)
            docs.extend(pdf_loader.load())
            docs.extend(txt_loader.load())

    if url:
        web_loader = WebBaseLoader(url)
        docs.extend(web_loader.load())
        
    print(f"从文件/URL加载了 {len(docs)} 个文档。")
    return docs

def create_vectorstore(docs):#创建RAG向量数据库
    if not docs:
        print("没有可用于创建向量数据库的文档。")
        return None

    print(f"正在为 {len(docs)} 个文档创建向量存储...")
    embedding = OllamaEmbeddings(
        model="nomic-embed-text", #本地语义模型
        base_url="http://localhost:8080"
    )
    doc_spliter = SemanticChunker(embeddings=embedding, add_start_index=True)
    chunks = doc_spliter.split_documents(docs)
    vectorstore = Chroma.from_documents(chunks, embedding, persist_directory=CHROMA_DB_DIR)
    print("向量存储创建完毕。")
    return vectorstore



if __name__== "__main__":
    # 需要更新RAG数据库时才运行此文件
    cleanup_chroma_db()#清理创建的Chroma DB，
    # 1. 从数据库加载文档
    conn = get_db_connection()
    db_docs = []
    if conn:
        try:
            db_docs = load_documents_from_db(conn)
        finally:
            conn.close()

    # 2. 从本地文件和URL加载文档 (请根据需要修改路径和URL)
    # 示例: file_path="your_folder", url="http://example.com"
    file_docs = load_file_url_documents(file_path=r'D:\下载\实训', url=None)

    # 3. 合并所有文档源
    all_docs = db_docs + file_docs
    
    if not all_docs:
        print("未能从任何来源加载到文档，程序退出。")
    else:
        # 4. 基于所有文档创建向量数据库
        vectorstore = create_vectorstore(all_docs)
        # 5. 保存向量数据库
        if vectorstore is not None and hasattr(vectorstore, "persist"):
            vectorstore.persist()
            print("向量数据库已保存到.")
        else:
            print("向量数据库未能保存。")