from langchain.docstore.document import Document
# from langchain.vectorstores import FAISS
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_community.document_loaders import DirectoryLoader, WebBaseLoader, PyPDFLoader, TextLoader, Docx2txtLoader, CSVLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
import os
import pymysql
import pymysql.cursors
import shutil
import sys
import io
import time
from config import settings

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
vectorstore = None

# 更新embedding配置
embedding = HuggingFaceEmbeddings(
    model_name="/app/models/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={
        'normalize_embeddings': True,
        'batch_size': 4  # 减小batch size防止内存问题
    }
)

DB_CONFIG = {
    'host': settings.DB_HOST,
    'user': settings.DB_USER,
    'password': settings.DB_PASSWORD,
    'db': settings.DB_NAME,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    try:
        server_conn_config = {k: v for k, v in DB_CONFIG.items() if k not in ['db', 'cursorclass']}
        server_conn = pymysql.connect(**server_conn_config)

        with server_conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['db']} CHARACTER SET utf8mb4")
            print(f"数据库 '{DB_CONFIG['db']}' 已准备就绪。")

        server_conn.close()
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
        if e.args[0] == 1146:
            print("数据库 'documents' 表不存在，将跳过从数据库加载。")
            return []
        else:
            print(f"数据库查询出错: {e}")
            raise

def cleanup_chroma_db():
    if os.path.exists(CHROMA_DB_DIR):
        shutil.rmtree(CHROMA_DB_DIR)
        print("已清理向量数据库目录：", CHROMA_DB_DIR)

def load_file_url_documents(file_path=None, url=None):
    docs = []
    if file_path:
        if os.path.isfile(file_path):
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

def create_chunks(docs):
    if not docs:
        print("没有可用于创建向量数据库的文档。")
        return []

    print(f"正在为 {len(docs)} 个文档创建向量存储...")
    doc_spliter = SemanticChunker(embeddings=embedding, add_start_index=True)
    chunks = doc_spliter.split_documents(docs)
    return chunks

# def create_vectorstore(chunks):
#     vectorstore = Chroma.from_documents(chunks, embedding, persist_directory=CHROMA_DB_DIR)
#     print("向量存储创建完毕。")
#     return vectorstore

def create_vectorstore(chunks):
    # Clean up existing ChromaDB if it exists
    if os.path.exists(CHROMA_DB_DIR):
        shutil.rmtree(CHROMA_DB_DIR)
    vectorstore = Chroma.from_documents(chunks, embedding, persist_directory=CHROMA_DB_DIR)
    print("向量存储创建完毕。")
    return vectorstore

# def add_to_vectorstore(vectorstore, file_path):
#     file = load_file_url_documents(file_path=file_path, url=None)
#     file_chunk = create_chunks(file)
#     vectorstore.add_documents(file_chunk)
#     vectorstore.persist()
#     return vectorstore

def add_to_vectorstore(vectorstore, file_path):
    try:
        # 验证文件是否存在且非空
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            raise ValueError("文件无效或为空")

        file_docs = load_file_url_documents(file_path=file_path)
        if not file_docs:
            raise ValueError("无法从文件提取内容")

        file_chunk = create_chunks(file_docs)
        if not file_chunk:
            raise ValueError("无法创建有效文本块")

        # 添加重试机制
        for attempt in range(3):
            try:
                vectorstore.add_documents(file_chunk)
                vectorstore.persist()
                return vectorstore
            except Exception as e:
                if attempt == 2: raise
                time.sleep(1)

    except Exception as e:
        print(f"文件处理失败: {file_path} - {str(e)}")
        raise

# 初始化时加载的文档路径
file_docs = load_file_url_documents(file_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base"), url=None)
chunks = create_chunks(file_docs)