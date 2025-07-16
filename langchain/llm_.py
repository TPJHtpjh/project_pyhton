# from langchain_community.chat_models import ChatOpenAI
# os.environ["OPENAI_API_KEY"] = "your_api_key_here"
# llm = ChatOpenAI(model_name="gpt-3.5-turbo")
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM

from langchain_community.chat_models import ChatTongyi
import os
from langchain.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder  # 关键组件
)
from langchain_community.llms import FakeListLLM
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser, StrOutputParser
from langchain_community.callbacks import get_openai_callback
from pydantic import BaseModel

os.environ["DASHSCOPE_API_KEY"] = "sk-1c9ecdbc37244d809ce41861a47b4e76"
llm = ChatTongyi(model_name="qwen-turbo",dashscope_api_key=os.environ["DASHSCOPE_API_KEY"])
# LangChain LCEL (LangChain Expression Language) 链式调用示例

# llm_=ChatOpenAI(
#     model="your model_name_here",  # 替换为实际的模型名称
#     temperature=0.1, # 控制生成文本的随机性，0.0表示完全确定性
#     max_tokens=1000,  # 设置生成文本的最大长度
#     openai_api_key=os.environ["DEEPSEEK_API_KEY"],  # 替换为实际的OpenAI API密钥
#     openai_api_base="https://api.deepseek.com/v1/chat/completions"  # 替换为API的地址
# )
#result_=llm_.invoke("请写一首关于春天的诗歌")
#print(result_.content)
llm1 = FakeListLLM(responses=["The weather is great today.","Hello world!"                            "Good morning!"])
# llm2 = FakeListLLM(responses=["天气很好。","你好，世界！","早上好！"])


prompt1 = ChatPromptTemplate.from_template("翻译为{language}:{text}")
prompt2 = ChatPromptTemplate([
    ("system","you are a translator"),
    ("user","Translate to {language}: {text}"),
])
prompt3 = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("you are a poet"),
    HumanMessagePromptTemplate.from_template("I need a poem about{topic} in {language}"),
])
prompt4 = ChatPromptTemplate([
    ("system","you are a poet in {language}"),
    MessagesPlaceholder("messages")
])
topic=input("topic:")
fill_prompt4 = prompt4.format_prompt(
    messages =[("user",f"I need a poem about the {topic}")],
    language = "中文",
).to_messages()
for msg in fill_prompt4:
    print(f"[{msg.type.upper()}]{msg.content}")
print("*"*90)


parser = StrOutputParser()
parser1=JsonOutputParser()#返回json格式数据
class Person(BaseModel):#自定义输出结构体
    name:str
    age:int
parser2=PydanticOutputParser(pydantic_object=Person)#返回自定义pydantic模型
prompt_template='''
  提取用户姓名和年龄{input}
  回答{format_instructions}
'''
prompt_template=PromptTemplate(
    template=prompt_template,
    input_variables=["input"],
    partial_variables={"format_instructions":parser2.get_format_instructions()}
     )
chain4=prompt_template|llm|parser2
result5=chain4.invoke({"input":"张三今年18岁了，李四去年比他大一岁。"})
print(result5.name,result5.age)
chain2 = prompt2 | llm1 | parser
chain3 = prompt3 | llm1 | parser

result3 =chain3.invoke({"topic":"sea","language":"中文"})

result2=chain2.invoke({"language":"中文","text":"Hellod world!"})

result4 = prompt4.invoke({"messages":[("user","I need a poem about the sea")],"language":"中文","topic":"沙漠"})
# with get_openai_callback as cb:
result_fill_4=llm.invoke(fill_prompt4)#=LLMChain(llm=llm,prompt=prompt4)

# print(f"Total Tokens: {cb.total_tokens}")
# print(f"Prompt Tokens: {cb.prompt_tokens}")
# print(f"Completion Tokens: {cb.completion_tokens}")
# print(f"Total Cost (USD): ${cb.total_cost}")
print(f'''
       Result2: {result_fill_4}
       ''')







