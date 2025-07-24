import mysql.connector
from config import settings
from fastapi import HTTPException

def get_db_connection():
    """
    获取 MySQL 数据库连接
    如果连接失败，抛出 HTTP 500 错误
    """
    try:
        return mysql.connector.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
    except mysql.connector.Error as err:
        raise HTTPException(
            status_code=500,
            detail=f"数据库连接失败: {err}"
        )