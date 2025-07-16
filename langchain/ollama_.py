from langchain.prompts import(
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain.schema.output_parser import StrOutputParser
from langchain_ollama import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_community.document_loaders import TextLoader,WebBaseLoader,PyPDFLoader
from langchain_community.vectorstores import FAISS #
from langchain.chains import RetrievalQA# 检索问答链，结合检索和生成功能
from transformers import AutoTokenizer,AutoModel#Hugging Face的模型加载工具
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate,FewShotPromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_chroma import Chroma
import os
os.environ["OLLAMA_BASE_URL"] = "http://localhost:8080"
os.environ["USER_AGENT"] = "MyApp/1.0"  # 添加自定义UA
os.environ["ANONYMIZED_TELEMETRY"] = "False"  # 禁用ChromaDB遥测
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # 解决OpenMP冲突
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"  # 禁用transformers警告
# 设置日志级别
import logging
logging.basicConfig(level=logging.ERROR)  # 只显示ERROR以上级别日志
loader =TextLoader("D:\下载\data\公司制度.txt",encoding='utf-8')
# # 从网页加载
# loader = WebBaseLoader(["https://example.com"])
# web_docs = loader.load()
# # 从PDF加载
# loader = PyPDFLoader("path/to/document.pdf")
# pdf_docs = loader.load()
example_prompt=PromptTemplate(
    input_variables=["input","output"],
    template="input:{input}\noutput:{output}"
)
examples=[
    {"input": "happy", "output": "sad"},
    {"input": "tall", "output": "short"},
    {"input": "energetic", "output": "lethargic"},
    {"input": "sunny", "output": "gloomy"},
    {"input": "windy", "output": "calm"},
]

example_selector=SemanticSimilarityExampleSelector.from_examples(
    examples,
    OllamaEmbeddings(model='nomic-embed-text',base_url='http://localhost:8080'),
    Chroma,
    k=1
)
#反义词选择器
similar_prompt=FewShotPromptTemplate(
    example_prompt=example_prompt,
    example_selector=example_selector,
    prefix="Give the antonym of the every input",
    suffix="Input:{input}\nOutput:",
    input_variables=["input"]
)
print(similar_prompt.format(input="happy"))

print("````````````````")

docs = loader.load_and_split()
text_spliter =RecursiveCharacterTextSplitter(
    chunk_size=512,#每个分块最大字符数
    chunk_overlap=50,#分块间的重叠字符
    length_function=len,#计算长度的函数
)
chunks=text_spliter.split_documents(docs)
embeddings =OllamaEmbeddings(model='nomic-embed-text',base_url="http://localhost:8080")
vector_dc=FAISS.from_documents(chunks,embeddings) # 创建向量数据库，使用Ollama的嵌入模型
# vector_dc.save_local("faiss_index") # 保存向量数据库到本地
query='总则'
# 使用向量数据库进行相似度检索,similarity_search_with_score返回文档和分数
rvector_dc=vector_dc.similarity_search(query,k=3) 

for doc in rvector_dc:
    # 输出检索到的相关文档内容,#print(f"Score: {score}")分数
    print(doc.page_content)  
vector_db =FAISS.from_documents(docs,embeddings)
ollm=Ollama(model="deepseek-r1:7b",base_url="http://localhost:8080")
qa_chain = RetrievalQA.from_chain_type(  # 创建检索问答链，结合向量检索和文本生成
    llm=ollm,
    retriever=vector_db.as_retriever()  # 将向量数据库转换为检索器，用于查找相关文档
)
prompt=ChatPromptTemplate.from_messages([
    ("system","你是一个熟知人物历史的史官"),
    ("user","请介绍{person}的生平事迹")
])
parser=StrOutputParser()
chain=prompt | ollm | parser

result=chain.invoke({"person":"女娲"})
# result = qa_chain.invoke("总结报告核心风险点")
print("````````````````")
print(result)