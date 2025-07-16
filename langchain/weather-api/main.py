from fastapi import FastAPI, HTTPException,APIRouter
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
from datetime import datetime, timezone  # 修改导入语句
from typing import List




API_KEY="2b90b7ff30d8bcc16bbb673be7d88c20"
CACHE_EXPIRE_MINUTES=60#一小时
weather_cache={}

if not API_KEY:
    raise RuntimeError("未设置API_KEY环境变量")

class WeatherResponse(BaseModel):
    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    description: str
    icon: str
    timestamp: datetime

class ForecastItem(BaseModel):
    temperature: float
    feels_like: float
    humidity: int
    description: str
    icon: str
    timestamp: datetime
    

class ForecastResponse(BaseModel):
    city:str
    country:str
    fore_five:List[ForecastItem]

def _get_cache(city: str,is_forecast:bool=False):
    """获取有效缓存"""
    cache_key=f"{city.lower()}_forecast" if is_forecast else city.lower()
    cache_data = weather_cache.get(cache_key)
    if cache_data and (datetime.now() - cache_data["timestamp"]).seconds < CACHE_EXPIRE_MINUTES*60:
        return cache_data["data"]
    return None

'''
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
# 在应用启动时初始化缓存
@app.on_event("startup")
async def startup():
FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
# 添加缓存装饰器
@app.get("/weather/{city}", response_model=WeatherResponse, summary="获取城市天气")
@cache(expire=300) # 缓存5分钟
async def get_weather(city: str):
    ...获取天气代码
'''
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app:FastAPI):
    #启动时逻辑
    '''初始化缓存'''
    weather_cache.clear()
    yield
    #关闭时逻辑

app=FastAPI(title="天气预报",version="1.0.0",lifespan=lifespan)
router=APIRouter(prefix='/api',tags=["天气接口"])# 添加路由,前缀和标签
#创建APIRouer给路由分组
#router1=APIRouter(prefix='/api1',tags=["天气接口1"])
#router2=APIRouter(prefix='/api2',tags=["天气接口2"])
#app.include_router(router1)
#app.include_router(router2)


    

@router.get("/forecast/{city}",response_model=ForecastResponse,summary="获取城市5天天气")
async def get_forecast(city:str):
    cached=_get_cache(city,True)
    if cached:
        return cached
    url=f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric&lang=zh_cn"
    async with httpx.AsyncClient()as client:
        try:
            response=await client.get(url)
            response.raise_for_status()
            data=response.json()
            daily_data={}
            for item in data["list"]:
                date = datetime.fromtimestamp(item["dt"], timezone.utc).strftime("%Y-%m-%d")  # 修改这里
                if date not in daily_data:
                    daily_data[date] = {
                        "temp_min": item["main"]["temp_min"],
                        "temp_max": item["main"]["temp_max"],
                        "description": item["weather"][0]["description"],
                        "icon": item["weather"][0]["icon"]
                    }
                else:
                    daily_data[date]["temp_min"] = min(daily_data[date]["temp_min"], item["main"]["temp_min"])
                    daily_data[date]["temp_max"] = max(daily_data[date]["temp_max"], item["main"]["temp_max"])

            result_data = {
                "city": data["city"]["name"],
                "country": data["city"]["country"],
                "forecasts": [{
                    "date": date,
                    **details
                } for date, details in list(daily_data.items())[:5]]  # 取前5天数据
            }
            
            # 更新缓存（使用独立缓存键）
            weather_cache[f"{city.lower()}_forecast"] = {
                "data": result_data,
                "timestamp": datetime.now()
            }
            return result_data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404,detail="城市未找到")
            raise HTTPException(status_code=500,detail="天气服务不可用")
    

@router.get("/weather/{city}",response_model=WeatherResponse,summary="获取城市天气")
async def get_weather(city:str):
    cached=_get_cache(city)
    if cached:
        return cached
    url=f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=zh_cn"
    async with httpx.AsyncClient() as client:
        try:
            response= await client.get(url)
            response.raise_for_status()
            data=response.json()
            result_data= {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "timestamp": datetime.fromtimestamp(data["dt"], timezone.utc)  # 修改这里
            }
            weather_cache[city.lower()]={
                "data":result_data,
                "timestamp":datetime.now()
            }
            return result_data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404,detail="城市未找到")
            raise HTTPException(status_code=500,detail="天气服务不可用")
        except Exception as e:
            raise HTTPException(status_code=500,detail=str(e))

@router.get("/weather",summary="获取多个城市天气")
async def get_weather_for_cities(cities:str):
    city_list=cities.split(",")
    results=[]
    async with httpx.Asyncclient() as client:
        for city in city_list:
            cached =_get_cache(city)
            if(cached):
                results.append(cached)
                continue
            url=f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=zh_cn"
            try:
                response=await client.get(url)
                if response.status_code==200:
                    data =response.json()
                    cache_entry = {
                        "city": data["name"],
                        "temperature": data["main"]["temp"],
                        "description": data["weather"][0]["description"],
                    }
                    weather_cache[city.lower()] = {
                        "data": cache_entry,
                        "timestamp": datetime.now()
                    }
                    results.append(cache_entry)
            except:
                #忽略单个城市错误
                continue
    return results

@router.get("/weather/history",summary="获取历史查询记录")
async def get_history_weather():
    history=[]
    for city in weather_cache:
        history.append(f"{city}:{weather_cache[city]['data']}--{weather_cache[city]['timestamp']}")
    return history

app.include_router(router)#在启动前需要挂载路由

if __name__=="__main__":
  import uvicorn
  uvicorn.run(app,host="127.0.0.1",port=8000)