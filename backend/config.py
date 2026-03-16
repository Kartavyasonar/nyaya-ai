from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "NyayaAI"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    SECRET_KEY: str = "change-this-in-production"
    FRONTEND_URL: str = "http://localhost:3000"

    # MongoDB
    MONGODB_URL: str
    DB_NAME: str = "nyaya_ai"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama3-70b-8192"

    # Hugging Face
    HF_TOKEN: Optional[str] = None
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    TRANSLATION_MODEL: str = "Helsinki-NLP/opus-mt-hi-en"

    # Twilio WhatsApp
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"

    # JWT
    JWT_SECRET: str = "change-this-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Vector Store
    FAISS_INDEX_PATH: str = "./data/vectorstore/nyaya_index"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    TOP_K_RESULTS: int = 8

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 20

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    # Sentry
    SENTRY_DSN: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
