"""Application configuration using Pydantic Settings."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


def get_database_url() -> str:
    """Get database URL with absolute path."""
    # Get project root (parent of backend/)
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "data" / "kb.db"
    # Ensure data directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{db_path.absolute()}"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = get_database_url()
    
    # Storage
    S3_BUCKET_NAME: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    LOCAL_STORAGE_PATH: str = "./data/uploads"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:5174"
    
    # Security
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_CONTENT_TYPES: list[str] = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Agent
    ANTHROPIC_API_KEY: Optional[str] = None
    MAX_JOB_RUNTIME_MINUTES: int = 120
    MAX_JOB_COST_USD: float = 5.0
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 1.0
    
    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Document Processing
    ENABLE_PDF_EXTRACTION: bool = True
    ENABLE_DOCX_EXTRACTION: bool = True
    PDF_MAX_PAGES: int = 100
    PDF_TIMEOUT_SECONDS: int = 60
    DOCX_TIMEOUT_SECONDS: int = 30
    
    # Vector Embeddings (optional feature)
    ENABLE_EMBEDDINGS: bool = False
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Local model, no API cost
    EMBEDDING_BATCH_SIZE: int = 10
    EMBEDDING_SIMILARITY_THRESHOLD: float = 0.7
    EMBEDDING_DIMENSION: int = 384  # Dimension for all-MiniLM-L6-v2
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
