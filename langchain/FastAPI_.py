from fastapi import FastAPI,Query
import uvicorn
from typing import Optional,Union
from pydantic import BaseModel


app=FastAPI(
    name='first_API',
    description='这是一个简单的API',
    version='1.0.0'
)
@app.get("/")
async def root():
    return {"message": "Hello World"}
@app.get("/buy/{item_id}")
async def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
@app.post('/items')

def creat_item(item:Item):
    item_dict=item.model_dump()
    if item.tax:
        total=item.price+item.tax
        item_dict.update({"total":total})
    return item_dict

@app.post("/items",response_model=BaseModel)
def create_items(item: Item):
    
    return item

@app.get("/items/")
async def read_items(
    q:Union[str,None]=Query(
        default=None,
        alias="item-query",
        title="查询字符串",
        description="用于查询项的字符串",#元数据（title，description）
        min_length=3,
        max_length=50,
        regex="^fixedquery$"#用正则限制字符串
        )):
    #q:List[str]=Query(default=["FOO","Bar"])
    results={"items":[{"item_id":"Foo"},{"item_id":"Bar"}]}
    if q:
        results.update({"q":q})
    return results
    

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
