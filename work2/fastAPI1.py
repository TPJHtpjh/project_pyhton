import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os


app=FastAPI(title="用户管理API",version='1.0.0')

# --- 配置 ---
# 优化: 在生产环境中应使用环境变量来管理敏感数据
SECRET_KEY = os.environ.get("SECRET_KEY", "a-secure-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Pydantic 模型 ---
# 优化: 使用更清晰的名称，并分离API输出和数据库内部模型
class UserProfile(BaseModel):
    id: int
    username: str
    email: str

class UserInDB(UserProfile):
    password: str # 存储哈希后的密码

# --- 内存数据库 ---
# 提示: 对于生产应用，应替换为真实的数据库，如 PostgreSQL 或 MySQL
db: List[UserInDB] = []

# --- 应用启动事件 ---
@app.on_event("startup")
async def startup_event():
    initial_users = [
        {"id": 1, "username": "张三", "email": "zhangsan@example.com", "password": "123456"},
        {"id": 2, "username": "李四", "email": "lisi@example.com", "password": "123456"}
    ]
    for u in initial_users:
        if not any(user.id == u["id"] for user in db):
            hashed_password = bcrypt.hashpw(u["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.append(UserInDB(id=u["id"], username=u["username"], email=u["email"], password=hashed_password))

# --- 内部辅助函数 ---
def _find_user_by_email(email: str) -> Optional[UserInDB]:
    for user in db:
        if user.email == email:
            return user
    return None

def _find_user_by_username(username: str) -> Optional[UserInDB]:
    for user in db:
        if user.username == username:
            return user
    return None

def _find_user_by_id(user_id: int) -> Optional[UserInDB]:
    for user in db:
        if user.id == user_id:
            return user
    return None

# --- 安全 & 工具函数 ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- API 端点 ---
@app.post("/user/register", status_code=201, summary="用户注册")
async def register_user(username:str, email:str, password:str):
    if _find_user_by_username(username) or _find_user_by_email(email):
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在")
    
    # 优化: 使用更健壮的ID生成方式，而不是简单地依赖列表长度
    new_user_id = (max(user.id for user in db) + 1) if db else 1
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user = UserInDB(id=new_user_id, username=username, email=email, password=hashed_password)
    db.append(user)
    return {"user_id": new_user_id, "message": "注册成功"}

# 安全修复: 返回 UserProfile 模型，避免泄露密码哈希
@app.get("/user/email/{user_email}", response_model=UserProfile, summary="根据邮箱查找用户")
async def get_user_by_email(user_email:str):
    user = _find_user_by_email(user_email)
    if user:
        return user
    raise HTTPException(status_code=404, detail="用户不存在")

# 安全修复: 返回 UserProfile 模型，避免泄露密码哈希
@app.get("/user/username/{user_name}", response_model=UserProfile, summary="根据用户名查找用户")
async def get_user_by_username(user_name:str):
    user = _find_user_by_username(user_name)
    if user:
        return user
    raise HTTPException(status_code=404, detail="用户不存在")

@app.get("/user/log_in", status_code=200, summary="用户登录")
async def user_log_in(username_or_email: str, password: str):
    # 优化: 直接调用内部函数，并使用更通用的邮箱正则表达式
    user = None
    if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", username_or_email):
        user = _find_user_by_email(username_or_email)
    else:
        user = _find_user_by_username(username_or_email)
        
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="密码错误")

    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }

@app.get("/user/profile", response_model=UserProfile, summary="获取用户个人资料")
async def get_user_profile(user_id:int):
    # 安全提示: 在生产应用中，此端点应受保护。
    # 通常会从请求头获取JWT，验证后返回对应用户的信息，而不是允许通过ID查询任意用户。
    user = _find_user_by_id(user_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail="用户不存在")

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
