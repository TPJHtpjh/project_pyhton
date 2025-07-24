from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from database import get_db_connection
import mysql.connector
from datetime import datetime
import requests
from config import settings
from typing import Optional
from auth import get_current_user
from pydantic import BaseModel
import time

import logging
from fastapi import HTTPException
from fastapi.responses import JSONResponse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(tags=["提问"])
class QuestionRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None

def call_deepseek_api(messages: list):
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.7
    }
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API调用失败: {str(e)}")

@router.post("/ask")
async def ask_question(
    request: QuestionRequest,  # 改为接收请求体
    username: str = Depends(get_current_user)
):
    question = request.question
    conversation_id = request.conversation_id
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 获取用户ID
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        user_id = user["user_id"]

        # 新建或验证对话
        if not conversation_id:
            cursor.execute(
                "INSERT INTO conversations (user_id, title) VALUES (%s, %s)",
                (user_id, f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            )
            conversation_id = cursor.lastrowid
            conn.commit()
        else:
            cursor.execute(
                "SELECT 1 FROM conversations WHERE conversation_id = %s AND user_id = %s",
                (conversation_id, user_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # 保存用户消息
        cursor.execute(
            "INSERT INTO messages (conversation_id, content, is_user) VALUES (%s, %s, %s)",
            (conversation_id, question, True)
        )
        conn.commit()
        
        # 获取对话历史（最近10条）
        cursor.execute(
            "SELECT content, is_user FROM messages WHERE conversation_id = %s ORDER BY created_at DESC LIMIT 10",
            (conversation_id,)
        )
        history = [{"role": "user" if m["is_user"] else "assistant", "content": m["content"]} 
                  for m in reversed(cursor.fetchall())]
        
        # 调用AI并保存回复
        ai_response = call_deepseek_api(history)
        cursor.execute(
            "INSERT INTO messages (conversation_id, content, is_user) VALUES (%s, %s, %s)",
            (conversation_id, ai_response, False)
        )
        conn.commit()
        
        return {"conversation_id": conversation_id, "answer": ai_response}
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {err}")
    finally:
        cursor.close()
        conn.close()

def generate_conversation_title(messages: list, username: str) -> str:
    """使用AI根据对话内容生成标题"""
    try:
        # 提取最近的几条消息作为上下文
#         recent_messages = messages[-5:] if len(messages) > 5 else messages
#         context = "\n".join([f"{'用户' if m['is_user'] else 'AI'}: {m['content']}"
#                            for m in recent_messages])

        recent_messages = messages[-5:] if len(messages) > 5 else messages
        context = "\n".join([
            f"{'用户' if ('is_user' in m and m['is_user']) or ('role' in m and m['role'] == 'user') else 'AI'}: {m['content']}"
            for m in recent_messages
        ])
        # 调用AI生成标题
        prompt = f"""
        请根据以下对话内容生成一个简洁的标题(不超过9个字)，要求：
        1. 体现对话的核心主题
        2. 简明扼要
        3. 使用中文
        4. 回答有且只有标题

        对话内容：
        {context}
        """

        # 使用DeepSeek API生成标题
        response = call_deepseek_api([
            {"role": "system", "content": "你是一个专业的标题生成助手"},
            {"role": "user", "content": prompt}
        ])

        # 清理响应，确保标题简洁
        title = response.strip().replace('"', '').replace("标题:", "").strip()
        if len(title) > 9:
            title = title[:9] + "..."
        return title or f"{username}的对话"
    except Exception as e:
        logger.error(f"生成标题失败: {str(e)}")
        return f"{username}的对话 {datetime.now().strftime('%m-%d %H:%M')}"

from fastapi import UploadFile, File, Form
from typing import Optional
import shutil, uuid, os
from pathlib import Path
from RAG import create_chunks, add_to_vectorstore
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

from langchain_community.embeddings import HuggingFaceEmbeddings

from typing import List, Optional
from fastapi import UploadFile, File

from config import settings
CHROMA_DB_PATH = settings.CHROMA_DB_PATH

UPLOAD_DIR = Path(__file__).with_suffix('').parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/aisk")
async def ask_with_rag(

    question: str = Form(...),           # ← 从表单字段读取
    conversation_id: Optional[int] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    username: str = Depends(get_current_user)
#     request: QuestionRequest = Depends(),          # JSON 体
#     files: Optional[List[UploadFile]] = File(None),      # 可选文件
#     username: str = Depends(get_current_user),
):
    """
    文件内容会被切块、向量化，然后参与本次对话的 RAG 回答。
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # ---- 1. 复用 /api/ask 的“用户/对话”逻辑 ----
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        user_id = user["user_id"]

        if not conversation_id:
            cursor.execute(
                "INSERT INTO conversations (user_id, title) VALUES (%s, %s)",
                (user_id, f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            )
            conversation_id = cursor.lastrowid
            conn.commit()
        else:
            cursor.execute(
                "SELECT 1 FROM conversations WHERE conversation_id = %s AND user_id = %s",
                (conversation_id, user_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="无权访问此对话")

        # ---- 2. 保存用户消息 ----
        cursor.execute(
            "INSERT INTO messages (conversation_id, content, is_user) VALUES (%s, %s, %s)",
            (conversation_id, question, True)
        )
        conn.commit()

        # ---- 3. 处理上传文件（如果有） ----
        if files:
#             embedding = OllamaEmbeddings(model="nomic-embed-text")
            embeddings = HuggingFaceEmbeddings(
                model_name="/app/models/all-MiniLM-L6-v2",  # ← 本地离线模型
                model_kwargs={
                    'device': 'cpu',
                    'local_files_only': True
                },
                encode_kwargs={
                    'normalize_embeddings': True,
                    'batch_size': 4
                }
            )
#             vectorstore = Chroma(
#                 persist_directory=str(CHROMA_DB_PATH),
#                 embedding_function=embeddings
#             )
#             for file in files:
#                 suffix = Path(file.filename).suffix
#                 local_path = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"
#                 with open(local_path, "wb") as buffer:
#                     shutil.copyfileobj(file.file, buffer)
#                 add_to_vectorstore(vectorstore, str(local_path))

            if os.path.exists(str(CHROMA_DB_PATH)):
                shutil.rmtree(str(CHROMA_DB_PATH))

            vectorstore = Chroma(
                persist_directory=str(CHROMA_DB_PATH),
                embedding_function=embeddings
            )

            for file in files:
                suffix = Path(file.filename).suffix
                local_path = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"

                try:
                    with open(local_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)

                    add_to_vectorstore(vectorstore, str(local_path))
                finally:
                    if os.path.exists(local_path):
                        os.remove(local_path)

        # ---- 4. 构造对话历史 ----
        cursor.execute(
            "SELECT content, is_user FROM messages WHERE conversation_id = %s ORDER BY created_at DESC LIMIT 10",
            (conversation_id,)
        )
        history = [
            {"role": "user" if m["is_user"] else "assistant", "content": m["content"]}
            for m in reversed(cursor.fetchall())
        ]

        logger.info(history)
        logger.info(len(history))
        if len(history) in [1, 5, 11]:
             new_title = generate_conversation_title(history, username)

             # 更新数据库中的标题
             cursor.execute(
                 "UPDATE conversations SET title = %s WHERE conversation_id = %s",
                 (new_title, conversation_id)
             )
             conn.commit()

        # ---- 5. RAG 回答 ----
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4}) if files else None
        if retriever:
            # 简单示例：把检索到的上下文拼到 system prompt
            docs = retriever.get_relevant_documents(question)
            context = "\n\n".join(d.page_content for d in docs)
            history.insert(0, {
                "role": "system",
                "content": f"以下知识来自用户刚上传的文件，请优先参考：\n{context}"
            })

        ai_response = call_deepseek_api(history)

        # ---- 6. 保存 AI 回答 ----
        cursor.execute(
            "INSERT INTO messages (conversation_id, content, is_user) VALUES (%s, %s, %s)",
            (conversation_id, ai_response, False)
        )
        conn.commit()

        return {"conversation_id": conversation_id, "answer": ai_response}

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {err}")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        )
    finally:
        cursor.close()
        conn.close()