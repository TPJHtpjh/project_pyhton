from langchain.memory import ConversationSummaryMemory
from langchain.chains import ConversationChain
from langchain.memory import ConversationEntityMemory
from langchain.memory.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE

from langchain_community.llms import Ollama

llm=Ollama(model="deepseek-r1:7b",
               base_url="http://127.0.0.1:8080")
def sum_conversation():
  sum_memory=ConversationSummaryMemory(llm=llm)

  sumconversation=ConversationChain(
    llm=llm,
    memory=sum_memory,
    verbose=False
  )

  s_long_conversation = [
  "我们公司的年假政策是,入职满1年有5天年假",
  "年假可以累积,但最多不超过10天",
  "申请年假需要提前至少1周提交",
  "病假需要提供医院证明",
  "年假和病假可以合并使用，但需经理批准"
  ]

  for i,con in enumerate(s_long_conversation):

    if(i%2==0):
        response=sumconversation.predict(input=con)
    else:
        sumconversation.memory.save_context(
            {'input':''},
            {'output':con}
        )

  print("\n当前记忆内容:")
  print(sum_memory.load_memory_variables({}))
  print("*"*90)
  print(f"摘要:{sum_memory.buffer}")
  query='年假最多积累多少天？'
  response=sumconversation.predict(input=query)
  print("*"*90)
  print(f"Human:{query}")
  print(f"AI:{response}")


def entity_conversation():
   entity_memory=ConversationEntityMemory(llm=llm)
   entity_conversation=ConversationChain(
      llm=llm,
      memory=entity_memory,
      prompt=ENTITY_MEMORY_CONVERSATION_TEMPLATE,
      verbose=True
   )
   entity_dialogue = [
     "张三是我们的HR经理",
     "张三负责处理请假申请",
     "请假需要发送邮件给张三",
     "李四是财务主管",
     "报销需要李四批准"]
   for i, con in enumerate(entity_dialogue):
        response=entity_conversation.predict(input=con)
        print(f'输入{con}')
        print(f'输出{response}')
        print('*'*50)
   print("记忆中的实体")
   for i,e in enumerate(entity_memory.store.items()):
      print(f'第{i}个实体,{e[0]}:{e[1]}')
   entity_query='请假需要联系谁？'
   entity_response=entity_conversation.predict(input=entity_query)
   print(f'输入{entity_query}')
   print(f'输出{entity_response}')

sum_conversation()

'''SimpleMemory'''
from langchain.memory import SimpleMemory
memory = SimpleMemory(memories={"foo": "bar"})
output = memory.load_memory_variables({})
print(output) # {'foo': 'bar'}

'''ReadOnlySharedMemory'''
from langchain.memory import ReadOnlySharedMemory, ConversationBufferMemory
memory = ConversationBufferMemory(memory_key="chat_history")
read_only_memory = ReadOnlySharedMemory(memory=memory)
memory.save_context({"input": "hello"}, {"output": "hi"})
result = read_only_memory.load_memory_variables({})
# result == memory.load_memory_variables({})

'''RunnableWithMessageHistory'''
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
store = {}
def get_session_history1(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]
llm = ChatOpenAI(model="gpt-3.5-turbo")
chain = RunnableWithMessageHistory(llm, get_session_history1)
response = chain.invoke(
{"input": "Hello, how are you?"},
config={"configurable": {"session_id": "abc123"}}
)
print(response)

'''ConversationBufferWindowMemory'''
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
store = {}
def get_session_history2(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]
memory = ConversationBufferWindowMemory(
chat_memory=store["session_id"],
return_messages=True,
k=3 # 保留最近3条记录
)
print(memory.memory_variables) # 输出记忆变量名
key = memory.memory_variables[0]
messages = memory.load_memory_variables({})[key]
# 更新会话历史
store["session_id"] = InMemoryChatMessageHistory(messages=messages)
llm = ChatOpenAI(model="gpt-3.5-turbo")
chain = RunnableWithMessageHistory(llm, get_session_history2)
response = chain.invoke(
{"input": "What's the weather today?"},
config={"configurable": {"session_id": "abc123"}}
)
print(response)

'''自定义记忆类'''
'''
必须实现四个核心方法：
memory_variables : 返回记忆变量名列表
load_memory_variables : 加载记忆内容
save_context : 保存输入/输出到记忆
clear : 清空记忆
'''
from langchain_core.memory import BaseMemory
from typing import Any, Dict, List
# 由于CustomMemory继承自BaseMemory，必须实现clear方法，否则会报错
class CustomMemory(BaseMemory):
    memories: Dict[str, Any] = {}

    @property
    def memory_variables(self) -> List[str]:
        return list(self.memories.keys())

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return self.memories

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]):
        for key in inputs:
            self.memories[key] = inputs[key]
        for key in outputs:
            self.memories[key] = outputs[key]

    def clear(self):
        self.memories.clear()

custom_memory = CustomMemory()
custom_memory.save_context({"input": "hello"}, {"output": "hi"})
output = custom_memory.load_memory_variables({})
print(output)  # {'input': 'hello', 'output': 'hi'}

