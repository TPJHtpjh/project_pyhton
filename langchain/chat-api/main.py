from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from typing import List, Dict, Optional
import uuid
import asyncio
import os
from datetime import datetime

app = FastAPI(title="实时聊天系统", version="1.0.0")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全配置
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 用户模型
class User(BaseModel):
    username: str
    password: str

# 消息模型
class Message(BaseModel):
    sender: str
    content: str
    timestamp: datetime = datetime.now()

# 模拟用户数据库
fake_users_db = {
    "alice": {
        "username": "alice",
        "password": "alicepassword"
    },
    "bob": {
        "username": "bob",
        "password": "bobpassword"
    }
}

# 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.message_history: List[Message] = []

    async def connect(self, websocket: WebSocket, user: str):
        await websocket.accept()
        self.active_connections[user] = websocket
        await self.broadcast_system_message(f"{user} 加入了聊天室")

    def disconnect(self, user: str):
        if user in self.active_connections:
            del self.active_connections[user]
            asyncio.create_task(self.broadcast_system_message(f"{user} 离开了聊天室"))

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: Message):
        # 保存到历史记录
        self.message_history.append(message)
        # 广播给所有连接的用户
        for connection in self.active_connections.values():
            await connection.send_json(message.dict())

    async def broadcast_system_message(self, content: str):
        message = Message(sender="系统", content=content)
        await self.broadcast(message)

manager = ConnectionManager()

# 认证函数
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 创建JWT令牌
    access_token = jwt.encode(
        {"sub": form_data.username},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        user = await get_current_user(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(websocket, user)
    try:
        # 发送历史消息
        for msg in manager.message_history[-20:]:
            await websocket.send_json(msg.dict())
        while True:
            data = await websocket.receive_text()
            message = Message(sender=user, content=data)
            await manager.broadcast(message)
    except WebSocketDisconnect:
        manager.disconnect(user)

@app.get("/history", response_model=List[Message])
async def get_chat_history(limit: int = 50):
    return manager.message_history[-limit:]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)