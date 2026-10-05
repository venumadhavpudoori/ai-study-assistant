from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Study Assistant"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/study_assistant"

    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Auth settings
    SECRET_KEY: str = "ai-study-assistant-dev-secret-key-replace-in-production-12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours

    # Upload settings
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024 # 20 MB

    # RAG settings
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 80
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"
    GROK_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROK_BASE_URL: str = "https://api.x.ai/v1"
    GROK_MODEL: str = "grok-beta"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    OPENAI_API_KEY: Optional[str] = None

    # Retrieval settings
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_THRESHOLD: float = 0.7

    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
