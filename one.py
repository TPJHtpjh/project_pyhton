from langchain.docstore.document import Document
import gradio as gr
from langchain.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_ollama import OllamaEmbeddings
from langchain.chains import RetrievalQA,ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_experimental.text_splitter import SemanticChunker
import atexit
import os
import pymysql
import pymysql.cursors
from pandas._libs.ops import vec_binop
import pytesseract
from langchain.prompts import PromptTemplate
import shutil
from langchain_community.chat_models import ChatTongyi
from langchain.memory import ConversationSummaryMemory
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
llm=Ollama(model_name="deepseek-r1:7b",base_url="http://localhost:8080")
#llm = ChatTongyi(model_name="qwen-turbo",dashscope_api_key="sk-1c9ecdbc37244d809ce41861a47b4e76")
#llm=DeepSeekChat(model_name="deepseek-chat",api_key="") DeepSeek模型
CHROMA_DB_DIR = "./chroma_db"
vectorstore=None
# os.environ["USER_AGENT"] = "LangChain-App/1.0 (Windows NT 10.0; Win64; x64)"
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',      # <-- 修改为您的MySQL用户名
    'password': '153@TPJHtpjh', # <-- 修改为您的MySQL密码
    'db': 'dbabc',      # <-- 您希望使用的数据库名称
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
            pdf_loader = DirectoryLoader(file_path, glob="**/*.pdf", loader_cls=PyPDFLoader, use_multithreading=True)
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
        model="nomic-embed-text", 
        base_url="http://localhost:8080")
    doc_spliter = SemanticChunker(embeddings=embedding, add_start_index=True)
    chunks = doc_spliter.split_documents(docs)
    vectorstore = Chroma.from_documents(chunks, embedding, persist_directory=CHROMA_DB_DIR)
    print("向量存储创建完毕。")
    return vectorstore

class DocumentQA:
    def __init__(self,prompt_template):
        self.vectorstore = None
        self.qa_chain = None
        #在提示词中需要包含{chat_history}和{context}和{question}
        self.prompt_template = prompt_template
        self.memory=ConversationSummaryMemory(
            llm=llm,
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
            output_key="answer"
        )
        
    def init_with_vectorstore(self, vectorstore):
        self.vectorstore = vectorstore
        self.qa_chain=self.init_qa_chain()

    def init_qa_chain(self):
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized. Please call 'init_with_vectorstore' first.")

        if(self.prompt_template==""):#默认提示词
            prompt_template='''
            你是一名天文学家，你精通天文知识。
            请保持严谨性，在回答时不要出现任何错误。
            请根据以下已知信息，幽默地回答问题。
            历史对话：{chat_history}
            已知信息:
            {context}

            问题: {question}
            请优先使用中文回答。'''
        else:
            prompt_template = self.prompt_template

        prompttemplate=PromptTemplate.from_template(prompt_template)
        
        qa_chain=ConversationalRetrievalChain.from_llm(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_type="mmr", # 最大边际相关性
                search_kwargs={"k": 4} # 返回4个相关块
            ),
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": prompttemplate},
            verbose=True
        )
        return qa_chain
    
    def clear(self):
        if hasattr(self, 'memory'):
            self.memory.clear()
    
    def show_history(self):
        if self.memory.chat_memory.messages:
          # else:
          #     return self.memory.load_memory_variables({})
          lines=[]
          for item in self.memory.chat_memory.messages:
              lines.append(f"{item.type}:{item.content}")
          return "\n".join(lines)
        else:
            return "暂无历史"
    
    def ask(self,question):
        if hasattr(self, 'qa_chain') and self.qa_chain:
            return self.qa_chain.invoke({"question": question})
        else:
            return "QA chain not initialized. Please load documents first."

if __name__== "__main__":
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

        if vectorstore:
            # 5. 使用创建的向量数据库进行问答
            dqa = DocumentQA("")
            dqa.init_with_vectorstore(vectorstore)
            
            # --- 以下为问答示例 ---
            print("\n--- 开始问答 ---")
            result1 = dqa.ask("微调大模型有哪些方法？")
            print("问题: 微调大模型有哪些方法？")
            if isinstance(result1, dict) and 'answer' in result1:
                print(f"回答: {result1['answer']}")
            else:
                print(f"回答: {result1}")

            result2 = dqa.ask("哪种最常用？")
            print("\n问题: 哪种最常用？")
            if isinstance(result2, dict) and 'answer' in result2:
                print(f"回答: {result2['answer']}")
            else:
                print(f"回答: {result2}")

            print("\n--- 对话历史 ---")
            print(dqa.show_history())
            
            dqa.clear()
            print("\n--- 清空历史后 ---")
            print(dqa.show_history())
            print("*"*90)
    
    # 清理创建的Chroma DB，如果不需要保留可以取消注释
    #atexit.register(cleanup_chroma_db)
'''def verify_answer(question, answer):
verification_prompt = f"""
请验证以下回答是否正确回答了问题：
问题：{question}
回答：{answer}
如果回答正确，输出"VALID"，否则输出"INVALID"并简要说明原因
"""
return model.generate(verification_prompt)'''


'''
from langchain.cache import GPUCache
from transformers import AutoTokenizer, AutoModelForCausalLM

# 自定义缓存
class KVOptCache(GPUCache):
    def __init__(self, size=1000):
        super().__init__(size)
        self.prefix_cache = {}  # 前缀缓存
    
    def lookup(self, prompt):
        # 查找最长匹配前缀
        for i in range(len(prompt), 0, -1):
            prefix = prompt[:i]
            if prefix in self.prefix_cache:
                return self.prefix_cache[prefix], prompt[i:]
        return None, prompt

# 使用优化缓存
llm = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-v0.1",
    cache_class=KVOptCache
)
'''


    