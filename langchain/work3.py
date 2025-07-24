import io
import sys
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_ollama import OllamaEmbeddings

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# 文档数据
db = [
    Document(page_content="流感症状包括发烧、咳嗽和肌肉疼痛", metadata={'disease':'流感'}),
    Document(page_content="糖尿病管理需要定期检测血糖水平", metadata={'disease':'糖尿病'}),
    Document(page_content="抗生素不能用于治疗病毒感染", metadata={'disease':'病毒感染'}),
    Document(page_content="正常血压范围是90/60mmHg到120/80mmHg", metadata={'disease':'血压'})
]

llm = Ollama(model="deepseek-r1:7b",
            base_url="http://localhost:8080",
            num_gpu=30)

def create_refine_prompts():
    """创建 refine 链所需的两个提示模板"""
    # 初始问题提示
    question_prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""
        你是一个医疗AI助手，需要遵守以下规则：
        1. 不能提供具体的药物建议
        2. 当问题涉及药物时，引导患者咨询医生
        3. 基于专业医学知识回答问题
        根据以下上下文回答问题：
        {context}
        
        问题：{question}
        初步回答：
        """
    )
    
    # 精炼提示
    refine_prompt = PromptTemplate(
        input_variables=["question", "existing_answer", "context"],
        template="""
        你已经有一个初步回答：
        {existing_answer}
        
        根据以下额外上下文，精炼你的回答：
        {context}
        
        原始问题：{question}
        请给出更完善的回答：
        """
    )
    
    return question_prompt, refine_prompt

def create_qa_chain():
    # 文档分割
    splitter = CharacterTextSplitter(
        chunk_size=50,
        chunk_overlap=10
    )
    
    # 嵌入模型
    embedding = OllamaEmbeddings(
        model='bge-m3',
        base_url="http://localhost:8080"
    )
    
    # 分割文档并创建向量库
    chunks = splitter.split_documents(db)
    vectorstore = FAISS.from_documents(
        chunks,
        embedding
    )
    
    # 检索器配置
    retriever = vectorstore.as_retriever(
        search_type='mmr',
        search_kwargs={
            'k': 3,  # 返回更多结果供精炼
            'filter': {'disease': '流感'},#只选出‘流感’类
            'fetch_k': 5,
            'lambda_mult': 0.3
        }
    )
    
    # 创建 refine 链所需的提示
    question_prompt, refine_prompt = create_refine_prompts()
    
    # 创建问答链
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='refine',  # 使用 refine 链
        retriever=retriever,
        chain_type_kwargs={
            'question_prompt': question_prompt,
            'refine_prompt': refine_prompt,
            'document_variable_name': 'context'  # 明确指定文档变量名
        },
        return_source_documents=True,
        input_key="query"  # 明确指定输入键
    )

if __name__ == '__main__':
    chain = create_qa_chain()
    
    # 查询示例
    query = '如果我发烧且肌肉疼痛，该吃什么药？'
    
    try:
        # 正确调用方式
        result = chain.invoke({"query": query})
        
        # 处理结果
        print(f"问题: {query}")
        print(f"回答: {result['result']}")
        if result['source_documents']:
            print("来源文档:")
            for doc in result['source_documents']:
                print(f"- {doc.page_content} (来源: {doc.metadata.get('disease', '未知')})")
    except Exception as e:
        print(f"查询失败: {str(e)}")