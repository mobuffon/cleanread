"""
Application configuration using Pydantic Settings
Loads from environment variables and .env file
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Project Info
    PROJECT_NAME: str = "CleanRead API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "change-this-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
        "http://localhost:8000",  # Backend itself
        "*",  # Allow all origins for production (same-domain deployment)
    ]

    # Database
    DATABASE_URL: str = "postgresql://cleanread:cleanread_dev@localhost:5432/cleanread"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Storage
    STORAGE_PATH: str = "./storage"
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    TRIAL_MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB for trial users
    USER_STORAGE_QUOTA: int = 50 * 1024 * 1024  # 50MB per user
    FILE_RETENTION_DAYS: int = 14  # Delete files after 2 weeks

    # PDF Processing
    PDF_MAX_PAGES: int = 500  # Max pages to process
    BATCH_MULTIPLIER: int = 2  # For GPU memory management

    # Email (Send to Kindle)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
