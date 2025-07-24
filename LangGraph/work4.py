import os
from langchain_community.llms import Ollama
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import Tool
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, TypedDict, Annotated
from langgraph.graph import add_messages
from langchain_tavily import TavilySearch
# 步骤1：定义状态类
class ChatState(TypedDict):
    messages: Annotated[List, add_messages]
TAVILY_API_KEY='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'
# 步骤2：创建LLM模型并绑定工具
llm=Ollama(
    model='deepseek-r1:7b',
    base_url='http://localhost:8080'
)
# # 初始化 TavilySearch 并传递 API 密钥
tavily_tool = TavilySearch(max_results=2, tavily_api_key=TAVILY_API_KEY)

# 定义工具
tools = [
    Tool(
        name="Web Search",
        func=tavily_tool.run,
        description="Useful for searching the web"
    )
]
# model_with_tools = llm.bind_tools(tools)

# 步骤3：创建聊天机器人节点函数
def chatbot_node(state: ChatState):
    last_message = state["messages"][-1]
    response = llm.invoke(last_message.content)
    return {"messages": [AIMessage(content=response)]}

# 步骤4：构建图结构
graph = StateGraph(ChatState)
graph.add_node("chatbot", chatbot_node)
graph.set_entry_point("chatbot")
graph.add_edge("chatbot", END)
app = graph.compile()

# 步骤5：调用图并获取响应
initial_state = {"messages": [HumanMessage(content="你好")]}
result = app.invoke(initial_state)
print("AI响应:", result["messages"][-1].content)