import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "192.168.18.2")
    DB_PORT: int = int(os.getenv("DB_PORT", "8306"))
    DB_USER: str = os.getenv("DB_USER", "LLM_DB")
    # DB_PASSWORD: str = os.getenv("DB_PASSWORD", "XDy982161")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "LLM_DB")
    # DB_NAME: str = os.getenv("DB_NAME", "ceshi")
    DB_NAME: str = os.getenv("DB_NAME", "LLM_DB")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "sk-dab0cb0c36594ba88b3aec41a4bbde6c")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CHROMA_DB_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

settings = Settings()