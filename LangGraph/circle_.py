import getpass
import os
from langgraph.graph import StateGraph, END,START# 状态图构建工具
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.llms import Ollama
from langchain_community.tools import TavilySearchResults
from typing import TypedDict, Annotated, List# Annotated复杂类型注解
from langchain_core.runnables import RunnableConfig
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import init_chat_model # 聊天模型初始化工具
from langchain_tavily import TavilySearch # Tavily搜索引擎工具
from langgraph.graph.message import add_messages # 消息列表处理工具
from langgraph.prebuilt import ToolNode, tools_condition # 预置工具节点和条件判断
langsmith_API_KEY='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'
# def _set_env(var: str):
#     if not os.environ.get(var):
#         os.environ[var] = getpass.getpass(f"{var}: ")
TAVILY_API_KEY='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'
# _set_env("TAVILY_API_KEY")
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

tool = TavilySearch(max_results=2)
tools = [tool]
# tool.invoke("What's a 'node' in LangGraph?")

'''
TypedDict
字段固定：只能包含定义好的键，不能添加额外的键。
类型检查：每个键的值必须符合定义的类型。
静态检查：在运行时仍然是普通的 dict,但在开发时可以通过类型检查工具发现问题。
'''
class Status(TypedDict):
    # 消息列表：使用Annotated和add_messages确保消息按顺序追加
    messages:Annotated[list, add_messages]

llm=Ollama(
    model='deepseek-r1:7b',
    base_url='http://localhost:8080'
)

search_tool = TavilySearch(max_results=2, tavily_api_key=TAVILY_API_KEY)

tools=[search_tool]


# 创建代理 - 添加严格的格式指令
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

memory = MemorySaver()
def chatbot_node(state: Status):
    last_message = state["messages"][-1]
    user_input = last_message.content

    # 添加 <think></think> 部分
    think_part = f"<think>Processing user input: {user_input}</think>"

    try:
        # 调用代理，获取 LLM 的回答
        response = agent.invoke({"input": user_input})
        final_answer = response  # 最终回答
    except Exception as e:
        # 如果调用失败，返回错误信息
        final_answer = f"An error occurred: {str(e)}"

    # 拼接完整的回答
    full_response = f"{think_part}\n\n{final_answer}"

    # 返回消息
    return {"messages": [AIMessage(content=full_response)]}

# 构建状态图
graph = StateGraph(Status)
graph.add_node("chatbot", chatbot_node)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)
app = graph.compile()

if __name__ == "__main__":
    input = {"messages": [HumanMessage(content="你好")]}
    result = app.invoke(input)
    print('*' * 90)
    print(result["messages"][-1].content)
#     from IPython.display import Image, display
#     try:
#       display(Image(graph.get_graph().draw_mermaid_png()))
#     except Exception:
# # This requires some extra dependencies and is optional
#       pass