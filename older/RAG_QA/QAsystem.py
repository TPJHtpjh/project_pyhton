
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_community.chat_models import ChatTongyi
from langchain.memory import ConversationSummaryMemory
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from RAG import add_to_vectorstore
from langchain.chains import (
    ConversationalRetrievalChain,
    LLMChain,
    StuffDocumentsChain,
    MapReduceDocumentsChain
)
import os
import sys
#from langchain.cache import GPUCache
from RAG import llm




def handle_response(dp_response):
    return dp_response.split("<think>")[-1].split("</think>")[-1]
    
    
# 自定义缓存
# class KVOptCache(GPUCache):
#     def __init__(self, size=1000):
#         super().__init__(size)
#         self.prefix_cache = {}  # 前缀缓存
    
#     def lookup(self, prompt):
#         # 查找最长匹配前缀
#         for i in range(len(prompt), 0, -1):
#             prefix = prompt[:i]
#             if prefix in self.prefix_cache:
#                 return self.prefix_cache[prefix], prompt[i:]
#         return None, prompt
# # 使用优化缓存
# llm = AutoModelForCausalLM.from_pretrained(
#     "mistralai/Mistral-7B-v0.1",
#     cache_class=KVOptCache
# )

class DocumentQA:
    def __init__(self,prompt_template):
        self.vectorstore = None
        self.qa_chain = None
        #在提示词中需要包含{chat_history}和{context}和{question}
        self.prompt_template = prompt_template
        self.memory = ConversationSummaryMemory(
            llm=llm,
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
            output_key="answer"
        )

    def init_with_vectorstore(self, vectorstore):
        self.vectorstore = vectorstore
        self.qa_chain = self.init_qa_chain()

    def add_file(self, file_path):
        try:
            add_to_vectorstore(self.vectorstore, file_path)
            self.qa_chain = self.init_qa_chain()
        except Exception as e:
            print(f"向量化文件失败: {file_path}, 错误: {e}")

    def init_qa_chain(self):
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized. Please call 'init_with_vectorstore' first.")
        vector_retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 4}
        )
        map_prompt = PromptTemplate(
        input_variables=["context", "question", "chat_history"],
        template='''
        分析天文文档片段：
        历史对话：{chat_history}
        文档片段：{context}
        问题：{question}
        
        提取关键信息（保持严谨但幽默）：
        '''
        )
    
        # 定义reduce阶段提示
        reduce_prompt = PromptTemplate(
            input_variables=["summaries", "question", "chat_history"],
            template='''
            综合以下分析结果：
            历史对话：{chat_history}
            各片段分析：{summaries}
            原始问题：{question}
            
            给出最终回答（严谨且幽默）：
            '''
        )
        
        # 创建map_chain
        map_chain = LLMChain(
            llm=llm,
            prompt=map_prompt
        )
        
        # 创建reduce_chain
        reduce_chain = StuffDocumentsChain(
            llm_chain=LLMChain(
                llm=llm,
                prompt=reduce_prompt
            ),
            document_variable_name="summaries"
        )
        
        # 创建map_reduce链
        map_reduce_chain = MapReduceDocumentsChain(
            llm_chain=map_chain,
            combine_document_chain=reduce_chain,
            document_variable_name="context",
            return_intermediate_steps=False
        )
        
        # 创建对话式检索链
        return ConversationalRetrievalChain(
            retriever=vector_retriever,
            combine_docs_chain=map_reduce_chain,
            memory=self.memory,
            question_generator=LLMChain(
                llm=llm,
                prompt=PromptTemplate(
                    template="基于对话历史给出相关天文知识的回答：\n历史：{chat_history}\n新问题：{question}\n回答：",
                    input_variables=["chat_history", "question"]
                )
            ),
            return_source_documents=False
            )
        #if not self.prompt_template:
            
            # prompt_template='''
            # 你是一名大模型专家，你精通大模型知识。
            # 请保持严谨性，在回答时不要出现任何错误。
            # 请根据以下已知信息，回答问题。
            # 历史对话：{chat_history}
            # 已知信息:
            # {context}
            # 如果问题在已知信息中没有涉及，用你自己的知识库回答，不要编造。
            # 问题: {question}
            # 请优先使用中文回答。
            # '''
        # else:
        #     prompt_template = self.prompt_template

        #prompttemplate = PromptTemplate.from_template(prompt_template)
        
        # chunks 可能为 None，需判空
        # bm25_retriever = BM25Retriever.from_documents(chunks or [], k=4)
        # qa_chain = ConversationalRetrievalChain.from_llm(
        #     llm=llm,
        #     chain_type="map_reduce",
        #     # retriever=EnsembleRetriever(
        #     #     retrievers=[vector_retriever, bm25_retriever],
        #     #     weights=[0.7, 0.3]
        #     # ),
        #     retriever=vector_retriever,
        #     memory=self.memory,
        #     return_source_documents=True,
        #     combine_docs_chain_kwargs={
        #         "prompt": prompttempalte
        #     },
        #     verbose=False#调试用，设置为True会输出非常非常多的信息
        # )
        # return qa_chain

    def clear(self):
        if hasattr(self, 'memory'):
            self.memory.clear()

    def show_history(self):
        try:
            if self.memory.chat_memory.messages:
                lines = [f"{item.type}:{item.content}" for item in self.memory.chat_memory.messages]
                return "\n".join(lines)
            else:
                return "暂无历史"
        except Exception:
            return "历史记录获取失败"
    
    # def verify_answer(self,question,answer):
    #     verification_prompt = f"""
    #     请验证以下回答是否正确回答了问题：
    #     问题：{question}
    #     回答：{answer}
    #     如果回答正确，只输出"VALID"即可（除此之外不要输出任何其他内容），
    #     否则输出"INVALID"并简要说明原因
    #     """
    #     return llm.invoke(verification_prompt)

    def ask(self,question):
        if hasattr(self, 'qa_chain') and self.qa_chain:
            result=self.qa_chain.invoke({"question": question})
            response=result['answer']
            #用deepseek-r1模型时需要处理，取出深度思考的内容
            response=handle_response(response)
            #需要返回参考文档则在后加上\n{result["source_documents"]}
            return (f'{response}')
            # verify_result=self.verify_answer(question,result['answer'])
            # verify_result=handle_response(verify_result)
            # print('*'*90)
            # print(verify_result)
            # print('*'*90)
            # if('INVALID' not in verify_result):
            #     return result
            # else:
            #     # self.memory.chat_memory.messages.pop()
            #     reanswer=self.qa_chain.invoke(
            #         {"question": f'''
            #         对上一次问题{question}的回答{result['answer']}不够准确，
            #         理由是{verify_result}，请重新回答。
            #         '''})
            #     reanswer=handle_response(reanswer['answer'])
            #     return reanswer
            
        else:
            return "QA chain not initialized. Please load documents first."

