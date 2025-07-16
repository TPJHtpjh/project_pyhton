from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain.memory import ConversationSummaryMemory
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage
from langchain_ollama import OllamaEmbeddings
from RAG import CHROMA_DB_DIR 
import os
import sys
from langchain_community.llms import Ollama
from langchain.cache import GPUCache
from transformers import AutoTokenizer, AutoModelForCausalLM
llm=Ollama(model="deepseek-r1:7b",
base_url="http://localhost:8080",
max_tokens=40960)
#llm = ChatTongyi(model_name="qwen-turbo",dashscope_api_key="sk-1c9ecdbc37244d809ce41861a47b4e76")
#llm=DeepSeekChat(model_name="deepseek-chat",api_key="") DeepSeek模型

def handle_response(dp_response):
    if("<think>" in dp_response or "</think>" in dp_response):
        return dp_response.split("<think>")[-1].split("</think>")[-1]
    else:
        return dp_response

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

        if(self.prompt_template=="" or self.prompt_template==None):#默认提示词
            # prompt_template='''
            # 你是一名天文学家，你精通天文知识。
            # 请保持严谨性，在回答时不要出现任何错误。
            # 请根据以下已知信息，幽默地回答问题。
            # 历史对话：{chat_history}
            # 已知信息:
            # {context}
            # 如果问题在已知信息中没有涉及，用你自己的知识库回答，不要编造。
            # 问题: {question}

            # 请优先使用中文回答。'''
            prompt_template='''
            你是一名大模型专家，你精通大模型知识。
            请保持严谨性，在回答时不要出现任何错误。
            请根据以下已知信息，回答问题。
            历史对话：{chat_history}
            已知信息:
            {context}
            如果问题在已知信息中没有涉及，用你自己的知识库回答，不要编造。
            问题: {question}
            请优先使用中文回答。
            '''
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
    
    def verify_answer(self,question,answer):
        verification_prompt = f"""
        请验证以下回答是否正确回答了问题：
        问题：{question}
        回答：{answer}
        如果回答正确，只输出"VALID"即可（除此之外不要输出任何其他内容），
        否则输出"INVALID"并简要说明原因
        """
        return llm.invoke(verification_prompt)

    def ask(self,question):
        if hasattr(self, 'qa_chain') and self.qa_chain:
            result=self.qa_chain.invoke({"question": question})
            verify_result=self.verify_answer(question,result['answer'])
            verify_result=handle_response(verify_result)
            if(verify_result.strip()=='VALID'):
                return result
            else:
                # self.memory.chat_memory.messages.pop()
                reanswer=self.qa_chain.invoke(
                    {"question": f'''
                    对上一次问题{question}的回答{result['answer']}不够准确，
                    理由是{verify_result}，请重新回答。
                    '''})
                reanswer=handle_response(reanswer)
                return reanswer
            
        else:
            return "QA chain not initialized. Please load documents first."
    
    

if __name__== "__main__":
    
    # --- 加载在 RAG.py 中创建的向量数据库 ---
    #CHROMA_DB_DIR = "./chroma_db"
    
    if not os.path.exists(CHROMA_DB_DIR):
        print(f"错误: 向量数据库目录 '{CHROMA_DB_DIR}' 不存在。")
        print("请确保您已经成功运行了 RAG.py 来创建数据库。")
        exit()
        
    print("正在从磁盘加载向量数据库...")
    embedding = OllamaEmbeddings(model="nomic-embed-text",
    base_url="http://localhost:8080"
    )
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embedding
    )
    print("向量数据库加载成功！")
    # --- --------------------------------- ---
    
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


