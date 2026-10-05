import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "LifeBook AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # Security & Auth (Supports both standard and JWT-prefixed env vars)
    SECRET_KEY: str = "lifebook-super-secret-jwt-key-for-hackathon-2026"
    JWT_SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    JWT_ALGORITHM: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    JWT_EXPIRE_MINUTES: Optional[int] = None
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = "http://localhost:5173/auth/google/callback"

    # Database (Defaults to SQLite in local directory)
    DATABASE_URL: str = "sqlite:///./lifebook.db"
    
    # Storage
    STORAGE_DIR: str = "./storage"
    
    # AI Providers ("local", "openai", "gemini", "openrouter")
    AI_PROVIDER: str = "openrouter"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    STT_PROVIDER: str = "local"
    
    # Embedding / RAG Settings ("local", "openrouter", "openai")
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    RAG_TOP_K: int = 5
    RAG_MIN_RELEVANCE_SCORE: float = 0.20
    RAG_RRF_K: int = 60
    RAG_DEDUPLICATE_ENTRIES: bool = True
    
    # Demo Seed Settings
    DEMO_NAME: str = "Jothiram"
    DEMO_EMAIL: str = "jothiram@lifebook.ai"
    DEMO_PASSWORD: str = "LifeBook2026!"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    @property
    def effective_jwt_secret(self) -> str:
        return self.JWT_SECRET_KEY or self.SECRET_KEY

    @property
    def effective_jwt_algorithm(self) -> str:
        return self.JWT_ALGORITHM or self.ALGORITHM

    @property
    def effective_jwt_expire_minutes(self) -> int:
        return self.JWT_EXPIRE_MINUTES or self.ACCESS_TOKEN_EXPIRE_MINUTES

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
