from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatTongyi
from pydantic import BaseModel
from langchain_core.output_parsers import  PydanticOutputParser, StrOutputParser
from langchain_chroma import Chroma
from questionRAG import QUESTION_DB_DIR,embedding,chunks
from RAG import llm
import os
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.runnables import RunnablePassthrough, RunnableSequence, RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
#'''本地模型'''

def handle_response(dp_response):
    return dp_response.split("<think>")[-1].split("</think>")[-1]
#llm = ChatTongyi(model="qwen-turbo",api_key=SecretStr("sk-1c9ecdbc37244d809ce41861a47b4e76"))
#llm=DeepSeekChat(model_name="deepseek-chat",api_key="") DeepSeek模型
class question(BaseModel):
        content:str='换一个关键词试试'
        answer:str='None'
        difficulty:str='None'
           
class LLMseek:
    def __init__(self,prompt_template,vector_store):
        
        self.vector_store=vector_store
        if prompt_template:
            self.prompt=prompt_template
        else:
            self.prompt='''
            你是一名天文学题库检索助手，
            根据用户给出的关键词{word}
            在题库{context}中找出最适合的一个题目作为回答{format_question}。
            题目的难度为{difficulty}
            要求：
            除非题库为空，否则必须返回一个题目。
            如果题库为空，则返回'换一个关键词试试'
            不能对题目有任何更改。
            '''

    def init_chain(self):
        
        parser=PydanticOutputParser(pydantic_object=question)
        Prompt=PromptTemplate(
            template=self.prompt,
            input_variables=['context','word'],
            partial_variables={'format_question':parser.get_format_instructions()}
        )

        vector_retriever=self.vector_store.as_retriever(
            search_kwargs={"k": 5}
        )
        bm25_retriever=BM25Retriever.from_documents(chunks,k=5)
        retriever=EnsembleRetriever(
            retrievers=[bm25_retriever,vector_retriever],
            weights=[0.6,0.4]
        )
        chain=RunnableSequence({'context':retriever,'word':lambda x:x,'difficulty':lambda x:x if x else '随机'}|Prompt|llm|parser)
        # memory_history=ChatMessageHistory()
        # memory_chain=RunnableWithMessageHistory(
        #     chain,
        #     # 使用底层消息存储而非 memory 封装
        #     lambda session_id: memory_history,
        #     input_messages_key="question",
        #     history_messages_key="chat_history"
        # )
        #read_only_memory = ReadOnlySharedMemory(memory=base_memory) # 创建只读副本
        # chat_model = ChatOpenAI(
        #     openai_api_base="https://...",
        #     model_kwargs={"memory_type": "remembrall"} # 启用长期记忆
        # )
        self.chain=chain

    def seek_question(self,word):
        '''
        对于单个关键字检索一个问题
        返回question类
        question.content为题目
        question.answer为答案
        question.difficulty为难度
        '''
        try:
            if not word:
                raise ValueError("输入不能为空")#应该在前端就提醒不能为空
            if self.chain is  None:
                self.init_chain()
            result= self.chain.invoke(word)
        except ValueError as e:
            print(e)
            return question()
        return result

def personal_sum(responds):
    '''
    defaults结构：
    content    #题目内容 
    answer     #答案
    difficulty #难度
    respond    #作答情况
    '''
    sum_prompt='''
    你是一名错题分析助手，请根据答题情况{responds}
    总结出该同学在天文学相关知识方面的薄弱点和不足。
    回答格式：良好表现+知识不足+针对建议
    要求：
    语气不要太重。
    分析客观真实。
    语言简短，不要太啰嗦。
    '''
    parser=StrOutputParser()
    sum_chain=sum_prompt|llm|parser
    answer=sum_chain.invoke(responds)
    answer=handle_response(answer)
    return answer



if __name__=='__main__':
    if not os.path.exists(QUESTION_DB_DIR):
        print(f"错误: 向量数据库目录 '{QUESTION_DB_DIR}' 不存在。")
        print("请确保您已经成功运行了 RAG.py 来创建数据库。")
        exit()
    print('正在加载向量数据库...')
    question_vectorstore=Chroma(
        persist_directory=QUESTION_DB_DIR,
        embedding_function=embedding
    )
    print('向量数据库加载成功')
    print('*'*90)


    qs=LLMseek('',question_vectorstore)
    qs.init_chain()


    words=['地球','火星','月球','太阳','银河系','宇宙','牛郎星','织女星']

    for word in words:
        '''
        重点在seek_question函数，用于检索问题
        返回一个question类
        '''
        Question = qs.seek_question(word)
        if Question:
          print(Question.content+'\n'+Question.answer+'\n'+Question.difficulty)
          print('\n')
        #print(getattr(Question, 'content', '') + '' + getattr(Question, 'answer', ''))
    