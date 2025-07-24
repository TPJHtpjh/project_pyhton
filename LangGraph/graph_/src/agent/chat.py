from datetime import datetime
from http.client import HTTPException
import httpx
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages 
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatTongyi
from pydantic import SecretStr
from typing import TypedDict, Annotated, List
# llm=Ollama(model="deepseek-r1:7b",
# base_url="http://localhost:8080",
# num_gpu=30
# # ,num_predict=40960
# )
llm = ChatTongyi(model="qwen-turbo", api_key=SecretStr("sk-1c9ecdbc37244d809ce41861a47b4e76"))

WEATHER_API_KEY="2b90b7ff30d8bcc16bbb673be7d88c20"
# CACHE_EXPIRE_MINUTES=60#缓存一小时
# weather_cache={}

class ChatState(TypedDict):
    """State for the chat agent."""
    messages: Annotated[List[str], add_messages]
class WeatherState(TypedDict):
    city:str
    weather:str
    temperature:float
    timestamp: datetime

weather=StateGraph(WeatherState)

def chat_node(state:ChatState):
    last_message=state["messages"][-1]
    user_input=last_message.content

async def get_weather_node(state:WeatherState):
    state=state.copy()
    state["timestamp"]=datetime.now()
    city=state["city"]
    url=f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=zh_cn"
    async with httpx.AsyncClient()as client:
        try:
            response=await client.get(url)
            data=response.json()
             # 获取城市信息
            city_name = data["city"]["name"]
            country_code = data["city"]["country"]
            
            # 获取第一个预报点的天气数据
            first_forecast = data["list"][0]
            temperature = first_forecast["main"]["temp"]
            description = first_forecast["weather"][0]["description"]
            state['weather'] = f"{city_name}, {country_code} 的天气是 {description}，温度为 {temperature}°C"
            state['temperature'] = temperature
            # 返回处理后的数据
            return state
        except:
            raise HTTPException(detail="天气服务不可用")
weather=(StateGraph(WeatherState).add_node('wea_node',get_weather_node)
       .add_edge(START, 'wea_node')
       .add_edge('wea_node', END)
       .compile(name="Weather Graph"))



if __name__=="__main__":
    import asyncio
    result=asyncio.run(weather.ainvoke({"city":"beijing",'weather':"",'temperature':0.0,'timestamp':datetime.now()}))
    print(result)
