from fastapi import APIRouter, HTTPException, Depends
from database import get_db_connection
import mysql.connector
from typing import Optional
from auth import get_current_user

router = APIRouter(tags=["对话管理"])

@router.post("/conversations")
async def create_conversation(
    title: str = "未命名对话",
    username: str = Depends(get_current_user)
):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        cursor.execute(
            "INSERT INTO conversations (user_id, title) VALUES (%s, %s)",
            (user["user_id"], title)
        )
        conversation_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute(
            "SELECT * FROM conversations WHERE conversation_id = %s",
            (conversation_id,)
        )
        return cursor.fetchone()
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {err}")
    finally:
        cursor.close()
        conn.close()

@router.get("/conversations")
async def list_conversations(username: str = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        cursor.execute(
            "SELECT * FROM conversations WHERE user_id = %s ORDER BY created_at DESC",
            (user["user_id"],)
        )
        return cursor.fetchall()
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"数据库错误: {err}")
    finally:
        cursor.close()
        conn.close()

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    username: str = Depends(get_current_user)
):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 验证对话归属
        cursor.execute(
            """SELECT c.* FROM conversations c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.conversation_id = %s AND u.username = %s""",
            (conversation_id, username)
        )
        conversation = cursor.fetchone()
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在或无权访问")
        
        # 获取消息历史
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = %s ORDER BY created_at",
            (conversation_id,)
        )
        conversation["messages"] = cursor.fetchall()
        return conversation
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"数据库错误: {err}")
    finally:
        cursor.close()
        conn.close()

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    username: str = Depends(get_current_user)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 验证归属并删除
        cursor.execute(
            """DELETE FROM conversations 
            WHERE conversation_id = %s AND user_id = (
                SELECT user_id FROM users WHERE username = %s
            )""",
            (conversation_id, username)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="对话不存在或无权删除")
        conn.commit()
        return {"message": "删除成功"}
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {err}")
    finally:
        cursor.close()
        conn.close()

from fastapi import Form

@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: int,
    new_title: str = Form(..., min_length=1, max_length=50),
    username: str = Depends(get_current_user)
):
    """
    更新对话标题
    - conversation_id: 对话ID
    - new_title: 新标题(1-50个字符)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 验证对话归属
        cursor.execute(
            """SELECT 1 FROM conversations c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.conversation_id = %s AND u.username = %s""",
            (conversation_id, username)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="对话不存在或无权修改")

        # 更新标题
        cursor.execute(
            "UPDATE conversations SET title = %s WHERE conversation_id = %s",
            (new_title, conversation_id)
        )
        conn.commit()
        return {"message": "标题更新成功", "new_title": new_title}
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {err}")
    finally:
        cursor.close()
        conn.close()
