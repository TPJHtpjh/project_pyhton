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

