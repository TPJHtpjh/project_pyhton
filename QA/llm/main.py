from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import init_db
from auth import router as auth_router, get_current_user
from ai import router as ai_router
from conversations import router as conversations_router
from fastapi.routing import APIRoute
import time
from QASystem import app as qa_app

a = 10
app = FastAPI(
    title="天文问答系统",
    description="登录版天文问答系统（所有功能需认证）",
    version="1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "defaultModelRendering": "model",
        "displayRequestDuration": True,
        "filter": True,
    }
)

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="天文问答系统",
        version="1.0",
        description="登录版天文问答系统（所有功能需认证）",
        routes=app.routes,
    )
    
    # 修改安全方案
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # 为需要认证的路由添加安全要求
    for route in app.routes:
        if isinstance(route, APIRoute):
            if not any(d.dependency for d in route.dependencies if getattr(d, "dependency", None) == get_current_user):
                continue
            if "security" not in route.__dict__:
                route.security = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.on_event("startup")
async def startup():
    init_db()

app.mount("/api/qa", qa_app)

app.include_router(auth_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

# 打印所有路由路径
for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"路由路径: {route.path}")
        
"""
API 地址:http://127.0.0.1:8000/
交互文档:http://127.0.0.1:8000/docs
替代文档:http://127.0.0.1:8000/api/conversations

http://127.0.0.1:8001/api/docs

"""