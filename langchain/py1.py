# import dashscope

# dashscope.api_key = "***"
# response = dashscope.Generation.call(
#     model='qwen-turbo',
#     prompt='Hello world!'
# )
# print(response.output.text)  # 正常输出表示密钥有效
# -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host mirrors.aliyun.com
# 适用场景：快速原型验证
# # 1
from langchain.document_loaders import TextLoader
from langchain.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.llms import Ollama

import os
os.environ["OLLAMA_BASE_URL"] = "http://localhost:8080"
# # 加载文档
# loader = TextLoader(r"D:\下载\data\公司制度.txt",encoding='UTF-8')
# documents = loader.load()
# # 创建向量库（内存中）
# embeddings = OllamaEmbeddings(
#     model="nomic-embed-text:latest",
#     base_url="http://localhost:8080"
# )
# vectorstore = FAISS.from_documents(documents, embeddings)
# # 创建问答链
# qa = RetrievalQA.from_chain_type(
# llm=Ollama(model="deepseek-r1:7b",base_url="http://localhost:8080"),  # 使用Ollama的LLM
# chain_type="stuff",
# retriever=vectorstore.as_retriever()
# )
# # 使用示例
# print(qa.run("年假最少可以请几天？"))


# 2
# 适用场景：企业知识库
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader,UnstructuredFileLoader
# from langchain_community.vectorstores import Chroma
# from langchain.chains import ConversationalRetrievalChain
# from langchain.memory import ConversationBufferMemory
# from langchain_community.embeddings import OllamaEmbeddings
# # 加载多种文档
# file_path = r"D:\下载\data\员工手册.pdf"
# pdf_loader = PyPDFLoader(file_path)
# web_loader = WebBaseLoader(["https://example.com/福利政策"])
# documents = pdf_loader.load() + web_loader.load()
# # 文档分块处理
# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
# chunk_overlap=100)
# texts = text_splitter.split_documents(documents)
# embeddings = OllamaEmbeddings(
#     model="nomic-embed-text",
#     base_url="http://localhost:8080"
# )
# # 创建持久化向量库
# vectorstore = Chroma.from_documents(texts, embeddings,
# persist_directory="./db")
# # 添加对话记忆
# memory = ConversationBufferMemory(memory_key="chat_history",
# return_messages=True)
# # 创建带记忆的问答链
# qa = ConversationalRetrievalChain.from_llm(
#   llm=OllamaLLM(model="deepseek-r1:7b",base_url="http://localhost:8080"),
#   retriever=vectorstore.as_retriever(),
#   memory=memory
# )
# # 使用示例
# print(qa("年假政策是怎样的？")["answer"])
# print(qa("上次说的年假，最多能累积多少天？")["answer"]) # 能记住上下文

#3.
# 适用场景：企业级知识管理系统
import os
from langchain.document_loaders import DirectoryLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from qdrant_client import QdrantClient
from langchain.llms import Ollama
from langchain.vectorstores import Chroma
import pytesseract
# 环境配置
# os.environ["QDRANT_HOST"] = "localhost"
# os.environ["QDRANT_PORT"] = "6333"
# 批量加载文档
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 1. 加载文档
def load_documents(file_path):
    """加载多种格式的文档"""
    documents = []
    
    # 遍历目录
    for filename in os.listdir(file_path):
        file = os.path.join(file_path, filename)
        # 处理 PDF
        if filename.endswith(".pdf"):
            try:
                loader = PyPDFLoader(file)
                documents.extend(loader.load())
            except Exception as e:
                print(f"加载 PDF {file} 失败: {e}")
        
        # 处理文本
        elif filename.endswith(".txt"):
            try:
                loader = TextLoader(file, encoding="utf-8")
                documents.extend(loader.load())
            except Exception as e:
                print(f"加载文本 {file} 失败: {e}")
    
    return documents

# 2. 文档预处理
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
    add_start_index=True
)

# 3. 创建向量库
def create_vector_store(documents):
    """创建并持久化向量存储"""
    # 使用本地嵌入模型
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url='http://localhost:8080')
    
    # 分割文档
    texts = text_splitter.split_documents(documents)
    
    # 创建向量库
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    return vectorstore

# 4. 创建问答链
def create_qa_chain(vectorstore):
    """创建带来源引用的问答链"""
    qa = RetrievalQA.from_chain_type(
        llm=Ollama(model="deepseek-r1:7b", base_url='http://localhost:8080'),
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=True
    )
    return qa

# 主程序
if __name__ == "__main__":
    # 设置文档路径
    file_path = 'D:/下载/data/knowledge_base/'
    
    # 验证路径
    if not os.path.exists(file_path):
        print(f"错误：路径 {file_path} 不存在")
        exit(1)
    
    # 加载文档
    documents = load_documents(file_path)
    # print(f"成功加载 {len(documents)} 个文档")
    
    # 创建向量库
    vectorstore = create_vector_store(documents)
    
    # 创建问答链
    qa = create_qa_chain(vectorstore)
    
    # 使用示例
    result = qa.invoke({"query": "技术部门的晋升标准是什么？"})
    
    # 输出结果
    print(f"答案：{result['result']}")
    print("来源文档：")
    
    for doc in result['source_documents'][:3]:
        source = doc.metadata.get('source', '未知来源')
        page = doc.metadata.get('page', doc.metadata.get('start_index', '0'))
        print(f"- {source} (第{page}页)")