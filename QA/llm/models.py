from database import get_db_connection
import mysql.connector
from fastapi import HTTPException

def init_db():
    """
    初始化数据库表结构：
    1. 创建 users/conversations/messages 表（如果不存在）
    2. 创建默认匿名用户
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 创建用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 创建对话表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """)

        # 创建消息表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INT AUTO_INCREMENT PRIMARY KEY,
            conversation_id INT NOT NULL,
            content TEXT NOT NULL,
            is_user BOOLEAN NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
        )
        """)

        # 创建默认匿名用户（用于未登录时的占位）
        cursor.execute("SELECT 1 FROM users WHERE username = 'anonymous'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                ("anonymous", "anonymous@example.com", "")
            )

        conn.commit()
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"数据库初始化失败: {err}"
        )
    finally:
        cursor.close()
        conn.close()