import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database (SQLite for local dev without Docker)
    database_url: str = "sqlite:///./product_importer.db"
    
    # Redis (can be skipped for local testing)
    redis_url: str = "redis://localhost:6379"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379"
    celery_result_backend: str = "redis://localhost:6379"
    
    # App settings
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_hosts: list = ["localhost", "127.0.0.1", "*"]
    
    # Upload settings
    max_upload_size: int = 500000000  # 500MB
    csv_chunk_size: int = 10000  # rows per COPY operation


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
